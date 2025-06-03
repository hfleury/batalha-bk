import json
from typing import Optional, Dict, List, Any

import redis.asyncio as aioredis


class GameRedisRepository:
    def __init__(self) -> None:
        self.redis_client: aioredis.Redis = aioredis.Redis(
            host="redis-18007.crce196.sa-east-1-2.ec2.redns.redis-cloud.com",
            port=18007,
            decode_responses=True,
            username="default",
            password="fjwyDAlbXizVW7lFNdbYmLSUjoCT8ub6",
        )

    async def save_player_board(
        self, game_id: str, player_id: int, ships: Dict[str, List[str]]
    ) -> None:
        """Save the player's board ships positions

        Args:
            game_id (str): UUID of the game
            player_id (int): UUUID of the player
            ships (Dict[str, List[str]]): Dictionary of ships and their positions
        """
        key = f"game_id:{game_id}:player_board:{player_id}:board"
        value = json.dumps(ships)
        await self.redis_client.set(key, value)

    async def get_player_board(
        self, game_id: int, player_id: int
    ) -> Dict[str, List[str]]:
        key = f"game_id:{game_id}:player_board:{player_id}:board"
        value = await self.redis_client.get(key)
        if value is None or not isinstance(value, (str, bytes, bytearray)):
            return {}
        return json.loads(value)

    def get_opponent_id(self, game_id: int, player_id: int) -> int:
        return 2 if player_id == 1 else 1

    async def get_player_hits(
        self, game_id: int, player_id: int
    ) -> Dict[str, List[str]]:
        key = f"game_id:{game_id}:player_board:{player_id}:hits"
        value = await self.redis_client.get(key)
        if value is None or not isinstance(value, (str, bytes, bytearray)):
            return {}
        return json.loads(value)

    async def save_hit(
        self, game_id: int, player_id: int, ship_id: str, position: str
    ) -> None:
        key = f"game_id:{game_id}:player_board:{player_id}:hits"
        value = await self.redis_client.get(key)

        if value is None or not isinstance(value, (str, bytes, bytearray)):
            hits: Dict[str, List[str]] = {}
        else:
            hits = json.loads(value)

        if ship_id not in hits:
            hits[ship_id] = []
        if position not in hits[ship_id]:
            hits[ship_id].append(position)

        await self.redis_client.set(key, json.dumps(hits))

    async def push_to_queue(self, queue_name: str, player_id: int) -> None:
        await self.redis_client.rpush(queue_name, player_id)  # type: ignore

    async def pop_from_queue(self, queue_name: str) -> Optional[str]:
        player_id = await self.redis_client.lpop(queue_name)  # type: ignore
        return str(player_id) if player_id is not None else None  # type: ignore

    async def save_game_session(self, game_key: str, game_data: Any) -> None:
        await self.redis_client.set(game_key, json.dumps(game_data))
