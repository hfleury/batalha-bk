"""Concrete implementation of the GameRepository interface using Redis."""

import json
import logging
import uuid
from datetime import datetime
from typing import List

import redis.asyncio as aioredis

from src.domain.game import GameSession, GameInfo
from src.domain.player import Player
from src.api.v1.schemas.place_ships import ShipDetails
from src.application.repositories.game_repository import GameRepository
from src.config import settings


logger = logging.getLogger(__name__)


class GameRedisRepository(GameRepository):
    """A game repository that uses Redis for data storage.

    This class provides a concrete implementation of the GameRepository abstract
    base class, using an asynchronous Redis client to persist and retrieve
    game state.
    """

    def __init__(self) -> None:
        # TODO: Move Redis connection details to environment variables/configuration.
        self.redis_client: aioredis.Redis = aioredis.Redis(
            host=settings.redis.host,
            port=settings.redis.port,
            decode_responses=True,
            username=settings.redis.username,
            password=settings.redis.password,
        )

    async def save_player_board(
        self, game_id: str, player: Player, ships: List[ShipDetails]
    ) -> None:
        """Saves a player's board (ship placements) to Redis.

        Args:
            game_id: The unique identifier for the game.
            player: The player object.
            ships: A list of Ship objects representing the player's board.
        """

        key = f"game:{game_id}:player_id:{player.id}:ships"
        board_data = {ship.type: ship.positions for ship in ships}

        await self.redis_client.hset(key, mapping={
            "ships": json.dumps(board_data),
            "status": "ships_placed",
            "placed_at": datetime.utcnow().isoformat()
        })  # type: ignore[misc]

        await self.redis_client.expire(key, 86400)

    async def get_player_board(
        self, game_id: uuid.UUID, player_id: uuid.UUID
    ) -> dict[str, list[str]]:
        # Match the key format used in save_player_board
        key = f"game:{game_id}:player_id:{player_id}:ships"
        logger.debug(f"[get_player_board] Loading key: {key}")

        raw = await self.redis_client.hget(key, "ships")  # type: ignore
        if raw is None:
            return {}

        try:
            return json.loads(raw)
        except Exception as e:
            logger.error(f"Failed to parse board data: {e}")
            return {}

    async def get_game_board(
        self, game_id: uuid.UUID
    ) -> dict[str, dict[str, list[str]]]:
        key = f"game:{game_id}:board"
        logger.debug(f"AQUI ESTA A KEY TO REDIS {key}")
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
        key = f"game:{game_id}:player_board:{player}:hits"
        value = await self.redis_client.get(key)
        if value is None or not isinstance(value, (str, bytes, bytearray)):
            return {}
        return json.loads(value)

    async def save_hit(
        self, game_id: uuid.UUID, player: uuid.UUID, ship_id: str, position: str
    ) -> None:
        key = f"game:{game_id}:player_board:{player}:hits"
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
        payload = json.dumps({"player_id": str(player)})
        logger.debug(f"[push_to_queue] Queue payload: {payload}")
        await self.redis_client.rpush(queue_name, payload)  # type: ignore

    async def pop_from_queue(self, queue_name: str, player: uuid.UUID) -> None:
        logger.debug("ESTA NA POP FROM QUEUE")
        payload = json.dumps({"player_id": str(player)})
        logger.debug(f"ESSE O PAYLOAD {payload}")
        await self.redis_client.lrem(queue_name, 1, payload)  # type: ignore

    async def save_game_to_redis(
        self,
        game: GameSession,
    ) -> None:
        key = f"game:{game.game_id}"
        # Serialize the entire GameSession to JSON
        game_dict = game.to_serializable_dict()
        game_json = json.dumps(game_dict)
        logger.debug(f"Saving full game session to Redis key: {key}")
        logger.debug(f"Game JSON: {game_json}")

        try:
            await self.redis_client.set(key, game_json, ex=86400)  # 24h TTL
        except Exception as e:
            logger.error(f"Failed to save game to Redis: {e}")
            raise
        # game_dict = game.to_serializable_dict()
        # logger.debug(f"INSIDE SAVE GAME TO REDIS {game_dict}")
        # players = iter(game.players)
        # TODO add it to configuration
        # ttl_seconds = 86400  # 24h in seconds
        # try:
        #    await self.redis_client.hset(f"game:{str(game_dict["game_id"])}", mapping={
        #        "player1": str(next(players)),
        #        "player2": str(next(players)),
        #        "status": "waiting_for_ships",
        #        "created_at": datetime.utcnow().isoformat()
        #    })   # type: ignore[misc]
        # except Exception as e:
        #    logger.error(f"NAO SALVO O JOGO ERROR: {e}")

    async def load_game_session(self, game_id: uuid.UUID) -> GameSession | None:
        key = f"game:{game_id}"
        logger.debug(f"INSIDE THE LOAD GAME SESSION {key}")
        raw = await self.redis_client.get(key)  # type: ignore
        if not raw:
            logger.warning(f"No game session found for key: {key}")
            return None
        try:
            data = json.loads(raw)
            return GameSession.from_serialized_dict(data)
        except Exception as e:
            logger.error(f"Failed to deserialize game session: {e}")
            return None

    async def save_game_session(self, game: GameSession) -> None:
        key = f"game:{game.game_id}:session"
        logger.debug(f"[save_game_session] GameSession JSON {game.model_dump_json()}")
        await self.redis_client.set(key, game.model_dump_json(), ex=3600)

    async def get_opponent_from_queue(
        self, queue_name: str, player_id: uuid.UUID
    ) -> uuid.UUID | None:
        player = str(player_id)
        try:
            players = await self.redis_client.lrange(queue_name, 0, -1)  # type: ignore
        except Exception as e:
            logger.error(f"Redis lrange error in get_opponent_from_queue: {e}")
            return None

        for raw_data in players:  # type: ignore
            try:
                # decode if needed
                if isinstance(raw_data, bytes):
                    raw_data = raw_data.decode("utf-8")

                data = json.loads(raw_data)  # type: ignore
                opponent_id = data.get("player_id")
            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                logger.warning(f"Invalid payload in queue: {raw_data} | Error: {e}")
                continue

            if opponent_id and opponent_id != player:
                try:
                    return uuid.UUID(opponent_id)
                except ValueError:
                    logger.warning(f"Invalid UUID format in queue: {opponent_id}")
                    continue

        return None

    async def get_game_info(self, game_key: str) -> GameInfo:
        logger.debug(f"INSIDE GET GAME INFO {game_key}")
        raw = await self.redis_client.hgetall(f"game:{game_key}")   # type: ignore[misc]
        return GameInfo(
            game_id=game_key,
            player1_id=raw["player1"],
            player2_id=raw["player2"],
            status=raw["status"],
            created_at=raw["created_at"],
        )

    async def exist_player_on_game(self, game_id: str, player_id: str) -> bool:
        key: str = f"game:{game_id}:player_id:{player_id}:ships"
        logger.debug(f"KEY FOR THE EXIST PLAYER ON GAME {key}")
        exist: bool = await self.redis_client.exists(key)
        return exist
