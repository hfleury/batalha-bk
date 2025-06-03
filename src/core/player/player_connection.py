from src.core.interface.connection_protocol import ConnectionProtocol


class Player:
    def __init__(self, player_id: int, connection: ConnectionProtocol) -> None:
        self.player_id = player_id
        self.connection = connection

    async def send_message(self, message: str) -> None:
        await self.connection.send_message(message)

    async def close_connection(self) -> None:
        await self.connection.close_connection()
