import json
import redis

redis_client = redis.Redis(
    host='redis-18007.crce196.sa-east-1-2.ec2.redns.redis-cloud.com',
    port=18007,
    decode_responses=True,
    username="default",
    password="fjwyDAlbXizVW7lFNdbYmLSUjoCT8ub6",
)


def save_player_board(game_id: str, player_id: int, ships: dict[str, list[str]]) -> None:
    key = f"game_id:{game_id}:player_board:{player_id}:board"
    value = json.dumps(ships)
    redis_client.set(key, value)

def get_player_board(game_id: int, player_id: int) -> dict[str, list[str]]:
    key = f"game_id:{game_id}:player_board:{player_id}:board"
    value = redis_client.get(key)
    if value is None:
        return {}
    return json.loads(value)
