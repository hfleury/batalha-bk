import json
from typing import Dict, List, Union

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from src.game.connection_manager import connection_manager
from src.game.redis import GameRedisRepository
from src.player.models import Player

router = APIRouter()
redis_repo = GameRedisRepository()


@router.websocket("/ws/connect")
async def websocket_connection(websocket: WebSocket) -> None:
    """Handles WebSocket connections for players."""

    player_id = connection_manager.get_available_player_id()
    player = Player(player_id, websocket)
    connection_manager.add_player(player)

    await websocket.accept()
    print(f"Player {player_id} connected")
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
                    ships: Dict[str, List[str]] = payload.get("ships", {})
                    if not game_id or not ships:
                        await websocket.send_json(
                            {"status": "error", "message": "Missing game_id or ships"}
                        )
                        continue

                    if not validate_ships(ships):
                        await websocket.send_json(
                            {"status": "error", "message": "Invalid ship placement"}
                        )
                        continue

                    place_result = place_ships(game_id, player_id, ships)
                    await websocket.send_json(place_result)

                elif action == "start_game":
                    game_id = payload.get("game_id")
                    players: Dict[str, Dict[str, List[str]]] = payload.get(
                        "players", {}
                    )
                    if not game_id or not players:
                        await websocket.send_json(
                            {"status": "error", "message": "Missing game_id or players"}
                        )
                        continue

                    start_result = start_game(game_id, players)
                    await websocket.send_json(start_result)

                elif action == "get_game_info":
                    game_id = payload.get("game_id")
                    requesting_player_id = payload.get("player_id")
                    if not game_id or requesting_player_id is None:
                        await websocket.send_json(
                            {
                                "status": "error",
                                "message": "Missing game_id or player_id",
                            }
                        )
                        continue

                    result = redis_repo.get_player_board(game_id, requesting_player_id)
                    await websocket.send_json(result)

                elif action == "shoot":
                    game_id = payload.get("game_id")
                    shooter_id = payload.get("player_id")
                    target = payload.get("target")

                    if not game_id or shooter_id is None or not target:
                        await websocket.send_json(
                            {
                                "status": "error",
                                "message": "Missing game_id, player_id, or target",
                            }
                        )
                        continue

                    opponent_id = redis_repo.get_opponent_id(game_id, shooter_id)
                    opponent_board = await redis_repo.get_player_board(
                        game_id, opponent_id
                    )

                    if not opponent_board:
                        await websocket.send_json(
                            {"status": "error", "message": "Opponent board not found"}
                        )
                        continue

                    hit_result: Dict[str, Union[str, bool]] = {
                        "status": "miss",
                        "target": target,
                    }

                    for ship_id, positions in opponent_board.items():
                        if target in positions:
                            await redis_repo.save_hit(
                                game_id, opponent_id, ship_id, target
                            )
                            hits = await redis_repo.get_player_hits(
                                game_id, opponent_id
                            )
                            is_sunk = set(hits.get(ship_id, [])) == set(positions)

                            hit_result = {
                                "status": "hit",
                                "target": target,
                                "ship_id": ship_id,
                                "sunk": is_sunk,
                            }
                            break

                    await websocket.send_json(hit_result)

                else:
                    await websocket.send_json(
                        {"status": "error", "message": f"Unknown action: {action}"}
                    )

            except json.JSONDecodeError:
                await websocket.send_text("Invalid JSON format")

    except WebSocketDisconnect:
        print(f"Player {player_id} disconnected")
        connection_manager.remove_player(player_id)
        await connection_manager.broadcast(f"Player {player_id} has left.")
    except Exception as e:
        print(f"Error with Player {player_id}: {e}")
        await websocket.send_text(f"Error: {e}")
        connection_manager.remove_player(player_id)
        await connection_manager.broadcast(
            f"Player {player_id} has left due to error: {e}"
        )


async def place_ships(
    game_id: str, player_id: int, ships: Dict[str, List[str]]
) -> Dict[str, str]:
    """
    Receives and stores player's ship placements.
    """
    await redis_repo.save_player_board(game_id, player_id, ships)
    # TODO: trigger async DB persistence (message/event)
    return {"status": "OK", "message": f"Ships placed for player {player_id}"}


async def start_game(
    game_id: str, players: Dict[str, Dict[str, List[str]]]
) -> Dict[str, str]:
    """
    Initializes a new game state by saving each player's ship board.
    """
    for player_id_str, ships in players.items():
        player_id = int(player_id_str)
        await redis_repo.save_player_board(game_id, player_id, ships)
        # TODO: Save game start metadata in Redis/db

    return {"status": "OK", "message": f"Game {game_id} started"}


def validate_ships(ships: Dict[str, List[str]]) -> bool:
    """
    Placeholder for validating ship positions: check for overlaps, bounds, etc.
    """
    # TODO: Implement validation rules
    return True
