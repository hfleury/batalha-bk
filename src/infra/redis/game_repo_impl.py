import json
import uuid
import time
from typing import Any

import redis.asyncio as aioredis
from src.core.interface.game_repository import GameRepository
from src.core.domain.player import Player
from src.core.domain.ship import Ship


class GameRedisRepository(GameRepository):
    def __init__(self) -> None:
        self.redis_client: aioredis.Redis = aioredis.Redis(
            host="redis-18007.crce196.sa-east-1-2.ec2.redns.redis-cloud.com",
            port=18007,
            decode_responses=True,
            username="default",
            password="fjwyDAlbXizVW7lFNdbYmLSUjoCT8ub6",
        )

    async def save_player_board(
        self, game_id: str, player: Player, ships: list[Ship]
    ) -> None:
        """Save the player's board ships positions

        Args:
            game_id (str): UUID of the game
            player_id (int): UUUID of the player
            ships (Dict[str, List[str]]): Dictionary of ships and their positions
        """
        key = f"game_id:{game_id}:player_board:{player.id}:board"
        value = json.dumps(ships)
        await self.redis_client.set(key, value)

    async def get_player_board(
        self, game_id: uuid.UUID, player_id: uuid.UUID
    ) -> dict[str, list[str]]:
        key = f"game_id:{game_id}:player_board:{player_id}:board"
        value = await self.redis_client.get(key)
        if value is None or not isinstance(value, (str, bytes, bytearray)):
            return {}
        return json.loads(value)

    async def get_opponent_id(
        self, game_id: uuid.UUID, player: Player
    ) -> uuid.UUID | None:
        redis_key = f"game:{str(game_id)}"
        data = await self.redis_client.get(redis_key)

        if data is None:
            return None

        game_data = json.loads(data)
        player_ids = list(game_data["players"].keys())

        try:

            return uuid.UUID(next(pid for pid in player_ids if pid != str(player.id)))
        except StopIteration:
            return None

    async def get_player_hits(
        self, game_id: uuid.UUID, player: uuid.UUID
    ) -> dict[str, list[str]]:
        key = f"game_id:{game_id}:player_board:{player}:hits"
        value = await self.redis_client.get(key)
        if value is None or not isinstance(value, (str, bytes, bytearray)):
            return {}
        return json.loads(value)

    async def save_hit(
        self, game_id: uuid.UUID, player: uuid.UUID, ship_id: str, position: str
    ) -> None:
        key = f"game_id:{game_id}:player_board:{player}:hits"
        value = await self.redis_client.get(key)

        if value is None or not isinstance(value, (str, bytes, bytearray)):
            hits: dict[str, list[str]] = {}
        else:
            hits = json.loads(value)

        if ship_id not in hits:
            hits[ship_id] = []
        if position not in hits[ship_id]:
            hits[ship_id].append(position)

        await self.redis_client.set(key, json.dumps(hits))

    async def push_to_queue(self, queue_name: str, player: uuid.UUID) -> None:
        await self.redis_client.rpush(queue_name, player)  # type: ignore

    async def pop_from_queue(self, queue_name: str) -> str | None:
        player_id = await self.redis_client.lpop(queue_name)  # type: ignore
        return str(player_id) if player_id is not None else None  # type: ignore

    async def save_game_session(self, game_key: str, game_data: Any) -> None:
        await self.redis_client.set(game_key, json.dumps(game_data))

    async def save_game_to_redis(
        self,
        game_id: uuid.UUID,
        players_data: dict[str, dict[str, dict[str, list[str]]]],
    ) -> None:
        redis_key = f"game:{str(game_id)}"

        payload: dict[str, Any] = {
            "game_id": str(game_id),
            "start_datetime": int(time.time()),
            "end_datetime": None,
            "players": players_data,  # {str(player_id): {"board": ...}}
        }

        await self.redis_client.set(redis_key, json.dumps(payload))
