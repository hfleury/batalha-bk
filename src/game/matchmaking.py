import uuid
from typing import Optional, Dict, Any

from src.game.connection_manager import connection_manager
from src.game.redis import GameRedisRepository

redis_repo: GameRedisRepository = GameRedisRepository()
MATCHMAKING_QUEUE_KEY: str = "matchmaking_queue"


async def handle_join_queue(player_id: int) -> Dict[str, Any]:
    opponent_id: Optional[str] = await redis_repo.pop_from_queue(MATCHMAKING_QUEUE_KEY)

    if opponent_id is None or int(opponent_id) == player_id:
        await redis_repo.push_to_queue(MATCHMAKING_QUEUE_KEY, player_id)
        return {"status": "waiting", "message": "Waiting for opponent"}

    game_id: str = str(uuid.uuid4())
    game_key: str = f"game:{game_id}"
    game_data: Dict[str, Any] = {
        "game_id": game_id,
        "player1_id": int(opponent_id),
        "player2_id": player_id,
        "status": "awaiting_ships",
        "turn": int(opponent_id),
    }

    await redis_repo.save_game_session(game_key, game_data)

    await notify_player(
        int(opponent_id),
        "game_started",
        {"game_id": game_id, "opponent_id": player_id},
    )

    await notify_player(
        player_id,
        "game_started",
        {"game_id": game_id, "opponent_id": int(opponent_id)},
    )

    return {"status": "matched", "game_id": game_id}


async def notify_player(player_id: int, event: str, data: Dict[str, Any]) -> None:
    player = connection_manager.get_player(player_id)
    if player is None:
        return
    await player.websocket.send_json({"action": event, "data": data})
