# src/game/redis_repository.py

import json
from typing import Optional

import redis


class GameRedisRepository:
    def __init__(self):
        self.redis_client = redis.Redis(
            host='redis-18007.crce196.sa-east-1-2.ec2.redns.redis-cloud.com',
            port=18007,
            decode_responses=True,
            username="default",
            password="fjwyDAlbXizVW7lFNdbYmLSUjoCT8ub6",
        )

    def save_player_board(self, game_id: str, player_id: int, ships: dict[str, list[str]]) -> None:
        key = f"game_id:{game_id}:player_board:{player_id}:board"
        value = json.dumps(ships)
        self.redis_client.set(key, value)

    def get_player_board(self, game_id: int, player_id: int) -> dict[str, list[str]]:
        key = f"game_id:{game_id}:player_board:{player_id}:board"
        value = self.redis_client.get(key)
        if value is None:
            return {}
        return json.loads(value)

    def get_opponent_id(self, game_id: int, player_id: int) -> int:
        # Simple fixed logic — change if needed
        return 2 if player_id == 1 else 1

    def get_player_hits(self, game_id: int, player_id: int) -> dict[str, list[str]]:
        key = f"game_id:{game_id}:player_board:{player_id}:hits"
        value = self.redis_client.get(key)
        return json.loads(value) if value else {}

    def save_hit(self, game_id: int, player_id: int, ship_id: str, position: str):
        key = f"game_id:{game_id}:player_board:{player_id}:hits"
        value = self.redis_client.get(key)
        hits: dict[str, list[str]] = json.loads(value) if value else {}

        if ship_id not in hits:
            hits[ship_id] = []
        if position not in hits[ship_id]:
            hits[ship_id].append(position)

        self.redis_client.set(key, json.dumps(hits))
