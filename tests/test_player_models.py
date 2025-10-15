import uuid
from unittest.mock import AsyncMock, MagicMock, call

import pytest

from src.core.domain.player import Player


def test_Player_init() -> None:
    """
    Test that the Player.__init__ method correctly initialize a new Player instance
    """
    mock_ws = MagicMock()
    player_id = uuid.uuid4()
    player = Player(player_id, mock_ws)

    # assert (
    #    player.websocket is mock_ws
    # ), "Player.websocket shoulb be the same object as the provided mock"
    assert player.id == player_id


@pytest.mark.asyncio
async def test_player_send_message_success() -> None:
    """
    Test the Player.send_message method to ensure it correctly calls
    the websocket.send_text method with the provided message
    """
    mock_ws = AsyncMock()

    test_msg = "Message test"

    await mock_ws.send_message(message=test_msg)

    mock_ws.send_text.assert_called_once()
    mock_ws.send_text.assert_called_with(test_msg)

    assert mock_ws.send_text.call_args == call(test_msg)


@pytest.mark.asyncio
async def test_player_close_connection() -> None:
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
async def test_send_messagte_fail(capfd: pytest.CaptureFixture[str]) -> None:
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

    out, err = capfd.readouterr()
    assert err == ""
    assert out == f"Error sending message to Player {player_id}: Simulate send error"
