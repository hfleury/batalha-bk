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

        action = payload.get("action")
        if action:
            initial_response: StandardResponse = await game_service.handle_action(
                action, payload, player
            )
            await websocket.send_json(initial_response.to_dict())

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
        await websocket.send_json(handler_response.to_dict())


@router.websocket("/ws/connect")
async def websocket_connection(websocket: WebSocket) -> None:
    """Handles the WebSocket connection for a player."""
    trace_id = str(uuid.uuid4())
    logger.info(f"[{trace_id}] New connection established")
    await websocket.accept()

    player_id = None
    player = None
    e: BaseException | None = None  # type: ignore

    try:
        player_id, player = await _register_player(websocket, trace_id)
        if not player_id or not player:
            await websocket.close()
            return

        await _message_loop(websocket, player)

    except WebSocketDisconnect as e:
        logger.info(f"[{trace_id}] Player {player_id} disconnected: {e}")
    except Exception as exc:
        logger.error(f"[{trace_id}] ERROR for player {player_id}: {exc}")
        if websocket.client_state.name == "CONNECTED":
            await websocket.send_json({"status": "error", "message": str(exc)})
    finally:
        if player_id:
            queue_key = "matchmaking:queue"
            await game_repo.pop_from_queue(queue_key, player_id)
            conn_manager.remove_player(player_id)
