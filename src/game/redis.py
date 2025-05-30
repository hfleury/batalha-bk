import json
from typing import List
import redis

redis_client = redis.Redis(
    host='redis-18007.crce196.sa-east-1-2.ec2.redns.redis-cloud.com',
    port=18007,
    decode_responses=True,
    username="default",
    password="fjwyDAlbXizVW7lFNdbYmLSUjoCT8ub6",
)


def save_player_board(player_id: int, ships: List[List[str]]) -> None:
    key = f"player_board:{player_id}:board"
    value = json.dumps(ships)
    redis_client.set(key, value)
