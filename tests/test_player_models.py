from unittest.mock import AsyncMock, MagicMock, call

import pytest
from _pytest.capture import capfd

from src.player.models import Player


def test_Player_init():
    """
    Test that the Player.__init__ method correctly initialize a new Player instance
    """
    mock_ws = MagicMock()
    player_id = 1
    player = Player(player_id, mock_ws)

    assert player.websocket is mock_ws, (
        "Player.websocket shoulb be the same object as the provided mock"
    )
    assert player.player_id == player_id


@pytest.mark.asyncio
async def test_player_send_message_success():
    """
    Test the Player.send_message method to ensure it correctly calls
    the websocket.send_text method with the provided message
    """
    mock_ws = AsyncMock()

    player_id = 1
    player = Player(player_id, mock_ws)

    test_msg = "Message test"

    await player.send_message(message=test_msg)

    mock_ws.send_text.assert_called_once()
    mock_ws.send_text.assert_called_with(test_msg)

    assert mock_ws.send_text.call_args == call(test_msg)


@pytest.mark.asyncio
async def test_player_close_connection():
    """
    Test the Palyer.close_connection method to ensure it correctly
    calls the websocket.close method.
    """
    mock_ws = AsyncMock()

    player_id = 1
    player = Player(player_id=player_id, websocket=mock_ws)

    await player.close_connection()

    mock_ws.close.assert_called_once()


@pytest.mark.asyncio
@pytest.fixture
async def test_send_messagte_fail():
    """
    Test the Player.send_message method to ensure the RuntimeError is
    correctly handle and print the message
    """
    mock_ws = AsyncMock()
    mock_ws.send_text.side_effect = RuntimeError("Simulate send error")

    player_id = 1
    player = Player(player_id, mock_ws)
    tst_message = "Message test"

    with pytest.raises(RuntimeError, match="Simulate send error"):
        await player.send_message(tst_message)

    captured = capfd.readouterr()
    assert (
        captured.out
        == f"Error sending message to Player {player_id}: Simulate send error"
    )
