from typing import Protocol, runtime_checkable


@runtime_checkable
class ConnectionProtocol(Protocol):
    """
    Protocol that abstracts any player connection type.
    """

    async def send_message(self, message: str) -> None:
        """Send a message using websockets

        Args:
            message (str): the message to be send
        """
        pass

    async def close_connection(self) -> None:
        """Close the connection"""
        pass
