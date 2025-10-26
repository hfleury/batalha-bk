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


@router.websocket("/ws/connect")
async def websocket_connection(websocket: WebSocket) -> None:
    """Handles the WebSocket connection for a player."""
    trace_id = str(uuid.uuid4())
    logger.info(f"[{trace_id}] New connection established")
    await websocket.accept()

    player_id = None
    player_conn = None

    try:
        # Wait for the first message to get player_id
        data = await websocket.receive_text()
        try:
            payload = json.loads(data)
            player_id_str = payload.get("player_id")

            if not player_id_str:
                await websocket.send_json({
                    "status": "error",
                    "message": "player_id is required in first message"
                })
                await websocket.close()
                return

            # Convert string to UUID object
            try:
                player_id = uuid.UUID(player_id_str)
            except ValueError:
                await websocket.send_json({
                    "status": "error",
                    "message": "Invalid player_id format. Must be a valid UUID."
                })
                await websocket.close()
                return

            # Initialize player and connection with UUID object
            conn_websocket = WebSocketConnection(player_id, websocket)
            player = Player(id=player_id)
            player_conn = PlayerConnection(player=player, connection=conn_websocket)
            conn_manager.add_player(player_conn)

            logger.info(f"[{trace_id}] Player {player_id} connected and registered")

            # Process the initial action if present
            action = payload.get("action")
            if action:
                initial_response: StandardResponse = await game_service.handle_action(
                    action, payload, player
                )
                await websocket.send_json(initial_response.to_dict())

            # Continue listening for subsequent messages
            while True:
                data = await websocket.receive_text()
                payload = json.loads(data)
                action = payload.get("action")

                handle_response: StandardResponse = await game_service.handle_action(
                    action, payload, player
                )
                await websocket.send_json(handle_response.to_dict())

        except json.JSONDecodeError as e:
            logger.error(f"[{trace_id}] Invalid JSON ERROR: {e}")
            await websocket.send_json(
                {"status": "error", "message": "Invalid JSON format"}
            )
            await websocket.close()
            return

    except WebSocketDisconnect as e:
        logger.info(f"[{trace_id}] Player {player_id} disconnected: {e}")
        if player_id:
            queue_key = "matchmaking:queue"
            await game_repo.pop_from_queue(queue_key, player_id)
            conn_manager.remove_player(player_id)
            await conn_manager.broadcast(f"Player {player_id} has left.")
    except Exception as e:
        logger.error(f"[{trace_id}] ERROR for player {player_id}: {e}")
        if player_id:
            queue_key = "matchmaking:queue"
            await game_repo.pop_from_queue(queue_key, player_id)
            conn_manager.remove_player(player_id)
            await websocket.send_json(
                {"status": "error", "message": str(e)}
            )
            await conn_manager.broadcast(f"Player {player_id} has left due to error.")
