"""Responsable to handle all action"""

import json
import logging
import uuid

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from src.core.manager.connection_manager import ConnectionManager
from src.core.player.models import WebSocketConnection
from src.core.player.player_connection import Player, PlayerConnection
from src.core.services.game import GameService
from src.infra.redis.game_repo_impl import GameRedisRepository

router = APIRouter()
conn_manager = ConnectionManager()
game_repo = GameRedisRepository()
game_service = GameService(game_repo, conn_manager)
logger = logging.getLogger(__name__)


@router.websocket("/ws/connect")
async def websocket_connection(websocket: WebSocket) -> None:
    """Handles the WebSocket connection for a player.

    This function manages the entire lifecycle of a player's WebSocket connection.
    It accepts a new connection, assigns a player ID, and adds the player to the
    connection manager. It then enters a loop to listen for incoming messages
    (actions) from the player, processes them through the `game_service`, and
    sends back responses.

    It also handles disconnection events, ensuring that the player is cleanly
    removed from the game and connection manager.

    Args:
        websocket (WebSocket): The WebSocket connection instance for the client.
    """
    trace_id = str(uuid.uuid4())
    logger.info(f"[{trace_id}] New connection established")
    await websocket.accept()

    # TODO remove it because the player ID will come before connect to
    # the websocket server
    player_id = conn_manager.get_new_player_id()
    conn_websocket = WebSocketConnection(player_id, websocket)
    player = Player(player_id)
    player_conn = PlayerConnection(player=player, connection=conn_websocket)

    conn_manager.add_player(player_conn)

    await websocket.send_text(f"Welcome, Player {player_id}!")
    await conn_manager.broadcast(
        f"Player {player_id} has joined.", excluded_player_id=player_id
    )

    try:
        while True:
            try:
                data = await websocket.receive_text()
                payload = json.loads(data)
                action = payload.get("action")

                response = await game_service.handle_action(action, payload, player)
                await websocket.send_json(response.to_json())

            except json.JSONDecodeError as e:
                logger.error(f"[{trace_id}] Invalid JSON ERROR: {e}")
                await websocket.send_json(
                    {"status": "error", "message": "Invalid JSON format"}
                )
    except WebSocketDisconnect as e:
        logger.error(f"[{trace_id}] Disconnected {e}")
        queue_key = "matchmaking:queue"
        await game_repo.pop_from_queue(queue_key, player_id)
        conn_manager.remove_player(player_id)
        await conn_manager.broadcast(f"Player {player_id} has left.")
    except Exception as e:
        logger.debug("HENRIQUE FLEURY CARDOSO")
        logger.error(f"[{trace_id}] ERROR {e}")
        queue_key = "matchmaking:queue"
        await game_repo.pop_from_queue(queue_key, player_id)
        conn_manager.remove_player(player_id)
        await websocket.send_json({"status": "error", "message": str(e)})
        await conn_manager.broadcast(f"Player {str(player_id)} has left due to error.")
