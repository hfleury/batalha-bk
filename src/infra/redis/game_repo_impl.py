import json
import logging
import uuid

import redis.asyncio as aioredis

from src.core.domain.game import GameSession
from src.core.domain.player import Player
from src.core.domain.ship import Ship
from src.core.interface.game_repository import GameRepository

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
            host="redis-18007.crce196.sa-east-1-2.ec2.redns.redis-cloud.com",
            port=18007,
            decode_responses=True,
            username="default",
            password="fjwyDAlbXizVW7lFNdbYmLSUjoCT8ub6",
        )

    async def save_player_board(
        self, game_id: str, player: Player, ships: list[Ship]
    ) -> None:
        """Saves a player's board (ship placements) to Redis.

        Args:
            game_id: The unique identifier for the game.
            player: The player object.
            ships: A list of Ship objects representing the player's board.
        """
        key = f"game:{game_id}:player_board:{player.id}:board"
        # Convert list of Ship objects to the format expected by get_player_board
        board_data = {ship.name: ship.position for ship in ships}
        value = json.dumps(board_data)
        await self.redis_client.set(key, value)  # type: ignore

    async def get_player_board(
        self, game_id: uuid.UUID, player_id: uuid.UUID
    ) -> dict[str, list[str]]:
        key = f"game:{game_id}:player_board:{player_id}:board"
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
        game_dict = game.to_serializable_dict()
        logger.debug(f"INSIDE SAVE GAME TO REDIS {game_dict}")
        redis_key = f"game:{str(game_dict["game_id"])}"
        # TODO add it to configuration
        ttl_seconds = 86400  # 24h in seconds
        logger.debug(
            f"GAME TO SERIALIZABLE DICT JSON DUMPS {
                json.dumps(game.to_serializable_dict())
            }"
        )
        try:
            await self.redis_client.set(
                redis_key, json.dumps(game.to_serializable_dict()), ex=ttl_seconds
            )
        except Exception as e:
            logger.error(f"NAO SALVO O JOGO ERROR: {e}")

    async def load_game_session(self, game_id: uuid.UUID) -> GameSession | None:
        key = f"game:{game_id}:session"
        raw = await self.redis_client.get(key)  # type: ignore
        if not raw:
            return None
        return GameSession.model_validate_json(raw)  # type: ignore

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
