"""Responsable to handle all action"""

import json
import logging
import uuid

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from src.infrastructure.manager.connection_manager import ConnectionManager
from src.infrastructure.connection.websocket import WebSocketConnection
from src.infrastructure.connection.player_connection import PlayerConnection
from src.domain.player import Player
from src.application.services.game import GameService
from src.infrastructure.persistence.game_repo_impl import GameRedisRepository
from src.api.v1.schemas.place_ships import StandardResponse

router = APIRouter()
conn_manager = ConnectionManager()
game_repo = GameRedisRepository()
game_service = GameService(game_repo, conn_manager)
logger = logging.getLogger(__name__)

async def _register_player(
    websocket: WebSocket,
    trace_id: str
) -> tuple[uuid.UUID | None, Player | None]:
    """Handles the initial message, extracts player_id, and registers the player."""
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
            return None, None

        try:
            player_id = uuid.UUID(player_id_str)
        except ValueError:
            response = StandardResponse(
                action="register",
                status="error",
                message="Invalid player_id format. Must be a valid UUID.",
                data=None
            )
            await websocket.send_json(response.to_dict())
            return None, None

        conn_websocket = WebSocketConnection(player_id, websocket)
        player = Player(id=player_id)
        player_conn = PlayerConnection(player=player, connection=conn_websocket)
        conn_manager.add_player(player_conn)

        logger.info(f"[{trace_id}] Player {player_id} connected and registered")

        # 🔍 ALWAYS check if player is in an active game (whether they send an action or not)
        if await game_repo.is_player_in_active_game(player_id):
            game_id_str = await game_repo.redis_client.get(f"player:{player_id}:active_game")
            if game_id_str:
                game = await game_repo.load_game_session(uuid.UUID(game_id_str))
                if game and game.status != "finished":
                    # Check if opponent is still connected
                    opponent_id = await game_repo.get_opponent_id(uuid.UUID(game_id_str), player)
                    if opponent_id and conn_manager.is_player_connected(opponent_id):
                        # Resume the game
                        conn_manager.add_player_to_game(player_id, uuid.UUID(game_id_str))

                        # 🔔 Notify opponent that player has reconnected
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
                        await conn_manager.send_to_player(opponent_id, reconnection_msg.to_dict())
                        logger.info(f"Sent reconnection notification to opponent {opponent_id} for player {player_id}")

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
                        return player_id, player
                    else:
                        # Opponent is not connected - game is dead
                        logger.info(f"Opponent {opponent_id} is offline. Clearing dead game for {player_id}")
                        await game_repo.clear_player_active_game(player_id)
                        # Fall through to handle action or queue

        # Handle action if present
        action = payload.get("action")
        if action:
            initial_response: StandardResponse = await game_service.handle_action(
                action, payload, player
            )
            # If the action was successful and created/joined a game, associate with game
            if (action == "find_game_session" and
                initial_response.status in ["ready", "resume_game"] and
                initial_response.data and
                isinstance(initial_response.data, dict)):

                game_id_str = initial_response.data.get("game_id")
                if game_id_str:
                    try:
                        game_id = uuid.UUID(game_id_str)
                        conn_manager.add_player_to_game(player_id, game_id)
                    except ValueError:
                        logger.warning(f"Invalid game_id in response: {game_id_str}")

            await websocket.send_json(initial_response.to_dict())
            return player_id, player

        return player_id, player
    except json.JSONDecodeError as e:
        logger.error(f"[{trace_id}] Invalid JSON ERROR during registration: {e}")
        await websocket.send_json({
            "status": "error",
            "message": "Invalid JSON format"
        })
        return None, None
    except Exception as e:
        logger.error(f"[{trace_id}] Unexpected ERROR during registration: {e}")
        return None, None

async def _message_loop(
    websocket: WebSocket,
    player: Player
) -> None:
    """The main loop for processing subsequent messages."""
    while True:
        data = await websocket.receive_text()
        payload = json.loads(data)
        action = payload.get("action")

        handler_response: StandardResponse = await game_service.handle_action(
            action, payload, player
        )

        # 🔑 Automatically associate player with game when they perform game actions
        if action in ["place_ships", "shoot"] and payload.get("game_id"):
            try:
                game_id = uuid.UUID(payload["game_id"])
                conn_manager.add_player_to_game(player.id, game_id)
            except ValueError:
                logger.warning(f"Invalid game_id in {action}: {payload.get('game_id')}")

        await websocket.send_json(handler_response.to_dict())

async def notify_opponent_disconnection(disconnected_player_id: uuid.UUID) -> None:
    """Notify the opponent that their player has disconnected."""
    try:
        # Find active game for the disconnected player
        game_id_str = await game_repo.redis_client.get(f"player:{disconnected_player_id}:active_game")
        if not game_id_str:
            return

        game_id = uuid.UUID(game_id_str)
        game = await game_repo.load_game_session(game_id)
        if not game or game.status == "finished":
            return

        # Find opponent
        opponent_id = None
        for pid in game.players:
            if pid != disconnected_player_id:
                opponent_id = pid
                break

        if opponent_id and conn_manager.is_player_connected(opponent_id):
            disconnect_msg = StandardResponse(
                status="opponent_disconnected",
                message="Your opponent has disconnected. They can reconnect to continue the game.",
                action="opponent_disconnected",
                data={
                    "disconnected_player": str(disconnected_player_id),
                    "game_id": str(game_id),
                    "can_reconnect": True,
                    "reconnect_timeout_seconds": 300
                }
            )
            await conn_manager.send_to_player(opponent_id, disconnect_msg.to_dict())
            logger.info(f"Sent disconnection notification to opponent {opponent_id} for player {disconnected_player_id}")

            # TODO move to game_repo_impl and GameService that is the layer responsabel
            # to talk with repo.
            await game_repo.redis_client.setex(
                f"game:{game_id}:disconnection_timeout",
                300,  # 5 minutes
                str(disconnected_player_id)
            )
            logger.debug(f"Set disconnection timeout for game {game_id}")

    except Exception as e:
        logger.error(f"Error notifying opponent of disconnection: {e}")

@router.websocket("/ws/connect")
async def websocket_connection(websocket: WebSocket) -> None:
    """Handles the WebSocket connection for a player."""
    trace_id = str(uuid.uuid4())
    logger.info(f"[{trace_id}] New connection established")
    await websocket.accept()

    player_id = None
    player = None

    try:
        player_id, player = await _register_player(websocket, trace_id)
        if not player_id or not player:
            await websocket.close()
            return

        await _message_loop(websocket, player)

    except WebSocketDisconnect as e:
        logger.info(f"[{trace_id}] Player {player_id} disconnected: {e}")
        if player_id:
            await notify_opponent_disconnection(player_id)

    except Exception as exc:
        logger.error(f"[{trace_id}] ERROR for player {player_id}: {exc}")
        if websocket.client_state.name == "CONNECTED":
            await websocket.send_json({"status": "error", "message": str(exc)})
        if player_id:
            await notify_opponent_disconnection(player_id)

    finally:
        if player_id:
            queue_key = "game:queue"
            await game_repo.pop_from_queue(queue_key, player_id)
            conn_manager.remove_player(player_id)
