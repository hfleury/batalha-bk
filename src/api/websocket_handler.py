"""Responsable to handle all action"""

import json
import logging
import uuid

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from src.infrastructure.manager.connection_manager import ConnectionManager
from src.domain.player import Player
from src.application.services.game import GameService
from src.infrastructure.persistence.game_repo_impl import GameRedisRepository
from src.api.v1.schemas.place_ships import StandardResponse
from src.application.services.player_websocket import PlayerWebSocketService

router = APIRouter()
conn_manager = ConnectionManager()
game_repo = GameRedisRepository()
game_service = GameService(game_repo, conn_manager)
player_websocket_service = PlayerWebSocketService(game_repo, game_service, conn_manager)
logger = logging.getLogger(__name__)


async def _message_loop(
    websocket: WebSocket,
    player: Player
) -> None:
    """The main loop for processing subsequent messages."""
    while True:
        data = await websocket.receive_text()
        payload = json.loads(data)
        action = payload.get("action")
        logger.debug(f"PAYLOAD {payload}")
        handler_response: StandardResponse = await game_service.handle_action(
            action, payload, player
        )

        if action in ["place_ships", "shoot"] and payload.get("game_id"):
            try:
                game_id = uuid.UUID(payload["game_id"])
                if player and player.id:
                    conn_manager.add_player_to_game(player.id, game_id)
            except ValueError:
                logger.warning(f"Invalid game_id in {action}: {payload.get('game_id')}")

        await websocket.send_json(handler_response.to_dict())


async def notify_opponent_disconnection(disconnected_player_id: uuid.UUID) -> None:
    """Notify the opponent that their player has disconnected."""
    try:
        # Find active game for the disconnected player
        game_id_str = await game_repo.redis_client.get(
            f"player:{disconnected_player_id}:active_game"
        )
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
                message="Your opponent has disconnected.",
                action="opponent_disconnected",
                data={
                    "disconnected_player": str(disconnected_player_id),
                    "game_id": str(game_id),
                    "can_reconnect": True,
                    "reconnect_timeout_seconds": 300
                }
            )
            await conn_manager.send_to_player(opponent_id, disconnect_msg.to_dict())
            logger.info(
                f"Sent disconnection notification to opponent"
                f" {opponent_id} for player {disconnected_player_id}"
            )

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
        player_id, player = await player_websocket_service.register_player_connection(
            websocket,
            trace_id
        )
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
