import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict

from src.game.connection_manager import connection_manager
from src.game.redis import save_player_board, get_player_board
from src.player.models import Player

router = APIRouter()


@router.websocket("/ws/connect")
async def websocket_connection(websocket: WebSocket) -> None:
    """Handles WebSocket connections for players.

    Args:
        websocket (WebSocket): Websocket connection for the player.
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
            try:
                payload = json.loads(data)
                action = payload.get("action")

                if action == "place_ships":
                    game_id = payload.get("game_id")
                    ships = payload.get("ships", [])
                    result = await place_ships(game_id, player_id, ships)
                    await websocket.send_json(result)
                elif action == "start_game":
                    game_id = payload.get("game_id")
                    players = payload.get("players", {})

                    result = await start_game(game_id, players)
                    await websocket.send_json(result)
                elif action == "get_game_info":
                    game_id = payload.get("game_id")
                    requested_player_id = payload.get("player_id")
                    if game_id is not None and requested_player_id is not None:
                        result = get_player_board(game_id, requested_player_id)
                        await websocket.send_json(result)
                    else:
                        await websocket.send_json({
                            "status": "error",
                            "message": "Missing game_id or player_id"
                        })
                else:
                    await connection_manager.broadcast(
                        f"Player {player_id} says: {data}",
                        excluded_player_id=player.player_id,
                    )
            except json.JSONDecodeError:
                await websocket.send_text("Invalid JSON")
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


async def place_ships(game_id: str, player_id: int, ships: dict[str, list[str]]) -> Dict[str, str]:
    """
    Receives and stores player's ship placements.
    """

    save_player_board(game_id, player_id, ships)
    # TODO trigger async DB persistence(message/event)

    return {"status": "OK", "message": f"Ships placed for player {player_id}"}

async def start_game(game_id: str, players: dict[int, dict[str, list[str]]]) -> Dict[str, str]:
    """
    Initializes a new game state by saving each player's ship board.

    Args:
        game_id: Unique ID of the game.
        players: Dict mapping player_id to their ships.
    """

    for player_id_str, ships in players.items():
        player_id = int(player_id_str)  # In case keys are strings in JSON
        save_player_board(game_id, player_id, ships)
        # TODO: Save game start metadata in Redis/db

    return {"status": "OK", "message": f"Game {game_id} started"}
