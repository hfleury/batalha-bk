"""Test file for the players basic actions"""

import uuid
from unittest.mock import AsyncMock, MagicMock, call

import pytest

from src.infrastructure.connection.websocket import WebSocketConnection


def test_websocket_connection_init() -> None:
    """
    Test that WebSocketConnection.__init__ correctly initializes a new instance.
    """
    mock_ws = MagicMock()
    player_id = uuid.uuid4()
    conn = WebSocketConnection(player_id, mock_ws)

    assert (
        conn.websocket is mock_ws
    ), "WebSocketConnection.websocket should be the same object as the provided mock"
    assert conn.player_id == player_id


@pytest.mark.asyncio
async def test_websocket_connection_send_message_success() -> None:
    """
    Test WebSocketConnection.send_message correctly calls websocket.send_text.
    """
    mock_ws = AsyncMock()
    player_id = uuid.uuid4()
    conn = WebSocketConnection(player_id, mock_ws)

    test_msg = "Message test"
    await conn.send_message(message=test_msg)

    mock_ws.send_text.assert_called_once()
    mock_ws.send_text.assert_called_with(test_msg)
    assert mock_ws.send_text.call_args == call(test_msg)


@pytest.mark.asyncio
async def test_websocket_connection_close_connection() -> None:
    """
    Test WebSocketConnection.close_connection correctly calls websocket.close.
    """
    mock_ws = AsyncMock()
    player_id = uuid.uuid4()
    conn = WebSocketConnection(player_id, mock_ws)

    await conn.close_connection()

    mock_ws.close.assert_called_once()


@pytest.mark.asyncio
async def test_websocket_connection_send_message_fail(
    capfd: pytest.CaptureFixture[str],
) -> None:
    """
    Test WebSocketConnection.send_message correctly handles and logs a RuntimeError.
    """
    mock_ws = AsyncMock()
    mock_ws.send_text.side_effect = RuntimeError("Simulate send error")
    player_id = uuid.uuid4()
    conn = WebSocketConnection(player_id, mock_ws)

    test_message = "Message test"

    with pytest.raises(RuntimeError, match="Simulate send error"):
        await conn.send_message(test_message)

    out, err = capfd.readouterr()
    assert err == ""
    assert f"Error sending message to Player {player_id}: Simulate send error\n" in out
