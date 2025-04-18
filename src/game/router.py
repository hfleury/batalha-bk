from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from src.game.connection_manager import connection_manager
from src.player.models import Player

router = APIRouter()


@router.websocket("/ws/connect")
async def websocket_connection(websocket: WebSocket):
    """
    Handles Websocket connections
    """
    player_id = connection_manager.get_available_player_id()
    player = Player(player_id, websocket)
    connection_manager.add_player(player)

    await websocket.accept()
    print(f"PLayer {player_id} connect")
    await websocket.send_text(f"Welcome, Player {player_id}!")
    await connection_manager.broadcast(
        f"Player {player_id} has joined.", excluded_player_id=player.player_id
    )

    try:
        while True:
            data = await websocket.receive_text()
            print(f"Received from player {player_id}: {data}")
            await connection_manager.broadcast(
                f"Player {player_id} says: {data}", excluded_player_id=player.player_id
            )
    except WebSocketDisconnect:
        print(f"Player {player_id} disconnected")
        connection_manager.remove_player(player_id)
        await connection_manager.broadcast(f"Player {player_id} has left.")
    except Exception as e:
        print(f"Error with Player {player_id}: {e}")
        await websocket.send_text(f"Error {e}")
        connection_manager.remove_player(player_id)
        await connection_manager.broadcast(
            f"Player {player_id} has left due to an error {e}"
        )
