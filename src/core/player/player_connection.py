from src.core.interface.connection_protocol import ConnectionProtocol
from src.core.domain.player import Player


class PlayerConnection:
    def __init__(self, player: Player, connection: ConnectionProtocol) -> None:
        self.player = player
        self.connection = connection

    async def send_message(self, message: str) -> None:
        await self.connection.send_message(message)

    async def close_connection(self) -> None:
        await self.connection.close_connection()
