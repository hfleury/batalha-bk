"""Player WebSocket service containing business logic for WebSocket connections."""
import uuid
import logging
import json

from fastapi import WebSocket

from src.domain.player import Player
from src.domain.game import GameSession
from src.application.services.game import GameService
from src.infrastructure.persistence.game_repo_impl import GameRedisRepository
from src.infrastructure.manager.connection_manager import ConnectionManager
from src.infrastructure.connection.websocket import WebSocketConnection
from src.infrastructure.connection.player_connection import PlayerConnection
from src.api.v1.schemas.place_ships import StandardResponse

logger = logging.getLogger(__name__)


class PlayerWebSocketService:
    """Handles the business logic for player WebSocket connections."""

    def __init__(
        self,
        game_repo: GameRedisRepository,
        game_service: GameService,
        conn_manager: ConnectionManager
    ):
        """Initializes the service with required dependencies."""
        self.game_repo = game_repo
        self.game_service = game_service
        self.conn_manager = conn_manager

    async def register_player_connection(
        self,
        websocket: WebSocket,
        trace_id: str
    ) -> tuple[uuid.UUID | None, Player | None]:
        """Handles the initial message, extracts player_id, and registers the player."""
        player_id = await self._extract_and_validate_player_id(websocket, trace_id)
        if not player_id:
            return None, None

        player = await self._create_and_register_player(websocket, player_id, trace_id)

        # Handle reconnection logic
        reconnected = await self._handle_player_reconnection(
            websocket,
            player,
            player_id,
            trace_id
        )
        if reconnected:
            return player_id, player

        # Handle initial action if present
        action_handled = await self._handle_initial_action(websocket, player, player_id)
        if action_handled:
            return player_id, player

        return player_id, player

    async def _extract_and_validate_player_id(
        self,
        websocket: WebSocket,
        trace_id: str
    ) -> uuid.UUID | None:
        """Extract and validate player_id from first message."""
        try:
            data = await websocket.receive_text()
            payload = json.loads(data)
            player_id_str = payload.get("player_id")

            if not player_id_str:
                response = StandardResponse(
                    action="register",
                    status="error",
                    message="player_id is required in first message",
                    data=None
                )
                await websocket.send_json(response.to_dict())
                return None

            try:
                return uuid.UUID(player_id_str)
            except ValueError:
                response = StandardResponse(
                    action="register",
                    status="error",
                    message="Invalid player_id format. Must be a valid UUID.",
                    data=None
                )
                await websocket.send_json(response.to_dict())
                return None
        except json.JSONDecodeError as e:
            logger.error(f"[{trace_id}] Invalid JSON ERROR during registration: {e}")
            await websocket.send_json({
                "status": "error",
                "message": "Invalid JSON format"
            })
            return None
        except Exception as e:
            logger.error(f"[{trace_id}] Unexpected ERROR during registration: {e}")
            return None

    async def _create_and_register_player(
        self,
        websocket: WebSocket,
        player_id: uuid.UUID,
        trace_id: str
    ) -> Player:
        """Create and register player connection."""
        conn_websocket = WebSocketConnection(player_id, websocket)
        player = Player(id=player_id)
        player_conn = PlayerConnection(player=player, connection=conn_websocket)
        self.conn_manager.add_player(player_conn)
        logger.info(f"[{trace_id}] Player {player_id} connected and registered")
        return player

    async def _handle_player_reconnection(
        self,
        websocket: WebSocket,
        player: Player,
        player_id: uuid.UUID,
        trace_id: str
    ) -> bool:
        """Handle game reconnection logic. Returns True if reconnection was handled."""
        if not await self.game_repo.is_player_in_active_game(player_id):
            return False

        game_id_str = await self.game_repo.redis_client.get(
            f"player:{player_id}:active_game"
        )
        if not game_id_str:
            return False

        game = await self.game_repo.load_game_session(uuid.UUID(game_id_str))
        if not game or game.status == "finished":
            return False

        opponent_id = await self.game_repo.get_opponent_id(
            uuid.UUID(game_id_str),
            player
        )
        if not opponent_id or not self.conn_manager.is_player_connected(opponent_id):
            # Opponent is not connected - clear dead game
            logger.info(
                f"Opponent {opponent_id} is offline. Clearing dead game for {player_id}"
            )
            await self.game_repo.clear_player_active_game(player_id)
            return False

        # Resume the game
        self.conn_manager.add_player_to_game(player_id, uuid.UUID(game_id_str))
        await self._notify_opponent_reconnection(
            opponent_id,
            player_id,
            game,
            game_id_str
        )
        await self._send_resume_response(
            websocket,
            player_id,
            opponent_id,
            game,
            game_id_str
        )
        return True

    async def _notify_opponent_reconnection(
        self,
        opponent_id: uuid.UUID,
        player_id: uuid.UUID,
        game: GameSession,
        game_id_str: str
    ) -> None:
        """Notify opponent about player reconnection."""
        reconnection_msg = StandardResponse(
            status="opponent_reconnected",
            message="Your opponent has reconnected!",
            action="opponent_reconnected",
            data={
                "reconnected_player": str(player_id),
                "game_id": game_id_str,
                "current_turn": str(game.current_turn) if game.current_turn else None,
                "status": game.status
            }
        )
        await self.conn_manager.send_to_player(
            opponent_id,
            reconnection_msg.to_dict()
        )
        logger.info(
            f"Sent reconnection notification to opponent {opponent_id}"
            f" for player {player_id}"
        )

    async def _send_resume_response(
        self,
        websocket: WebSocket,
        player_id: uuid.UUID,
        opponent_id: uuid.UUID,
        game: GameSession,
        game_id_str: str
    ) -> None:
        """Send game resume response to player."""
        resume_response = StandardResponse(
            status="resume_game",
            message="Reconnected to existing game",
            action="game_resumed",
            data={
                "game_id": game_id_str,
                "status": game.status,
                "current_turn": str(game.current_turn) if game.current_turn else None,
                "your_player_id": str(player_id),
                "opponent_id": str(opponent_id),
                "opponent_connected": True
            }
        )
        await websocket.send_json(resume_response.to_dict())

    async def _handle_initial_action(
        self,
        websocket: WebSocket,
        player: Player,
        player_id: uuid.UUID
    ) -> bool:
        """Handle initial action from registration payload.
            Returns True if action was handled.
        """
        try:
            data = await websocket.receive_text()
            payload = json.loads(data)
            action = payload.get("action")

            if action:
                initial_response: StandardResponse = (
                    await self.game_service.handle_action(
                        action, payload, player
                    )
                )

                if (
                    action == "find_game_session" and
                    initial_response.status in ["ready", "resume_game"] and
                    initial_response.data and
                    isinstance(initial_response.data, dict)
                ):
                    game_id_str = initial_response.data.get("game_id")
                    if game_id_str:
                        try:
                            game_id = uuid.UUID(game_id_str)
                            self.conn_manager.add_player_to_game(player_id, game_id)
                        except ValueError:
                            logger.warning(
                                f"Invalid game_id in response: {game_id_str}"
                            )

                await websocket.send_json(initial_response.to_dict())
                return True
        except json.JSONDecodeError:
            # If we can't parse the message again, return False
            return False
        except Exception:
            return False

        return False
