import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, Any

from src.game.connection_manager import connection_manager
from src.game.redis import GameRedisRepository
from src.player.models import Player

router = APIRouter()
redis_repo = GameRedisRepository()


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

                    result = start_game(game_id, players)
                    await websocket.send_json(result)
                elif action == "get_game_info":
                    game_id = payload.get("game_id")
                    requested_player_id = payload.get("player_id")
                    if game_id is not None and requested_player_id is not None:
                        result = redis_repo.get_player_board(game_id, requested_player_id)
                        await websocket.send_json(result)
                    else:
                        await websocket.send_json({
                            "status": "error",
                            "message": "Missing game_id or player_id"
                        })
                elif action == "shoot":
                    game_id = payload["game_id"]
                    player_id = payload["player_id"]
                    target = payload["target"]

                    opponent_id =  redis_repo.get_opponent_id(game_id, player_id)
                    opponent_board =  redis_repo.get_player_board(game_id, opponent_id)

                    hit_result: dict[str, Any] = {"status": "miss", "target": target}

                    for ship_id, positions in opponent_board.items():
                        if target in positions:
                            redis_repo.save_hit(game_id, opponent_id, ship_id, target)
                            # Check if the ship is sunk
                            hits = redis_repo.get_player_hits(game_id, opponent_id)

                            is_sunk = set(hits.get(ship_id, [])) == set(positions)
                            hit_result = {
                                "status": "hit",
                                "target": target,
                                "ship_id": ship_id,
                                "sunk": is_sunk
                            }
                            break

                    await websocket.send_json(hit_result)
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


def place_ships(game_id: str, player_id: int, ships: dict[str, list[str]]) -> Dict[str, str]:
    """
    Receives and stores player's ship placements.
    """

    redis_repo.save_player_board(game_id, player_id, ships)
    # TODO trigger async DB persistence(message/event)

    return {"status": "OK", "message": f"Ships placed for player {player_id}"}

def start_game(game_id: str, players: dict[int, dict[str, list[str]]]) -> Dict[str, str]:
    """
    Initializes a new game state by saving each player's ship board.

    Args:
        game_id: Unique ID of the game.
        players: Dict mapping player_id to their ships.
    """

    for player_id_str, ships in players.items():
        player_id = int(player_id_str)  # In case keys are strings in JSON
        redis_repo.save_player_board(game_id, player_id, ships)
        # TODO: Save game start metadata in Redis/db

    return {"status": "OK", "message": f"Game {game_id} started"}
