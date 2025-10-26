# batalha-bk
The backend for the game Naval Battle, version 1 is a monolithic using Python and FastAPI

## Start
To start have installed the JustFile program, [here is the link](https://github.com/casey/just)
And have Poetry installed as well. [Poetry](https://python-poetry.org/)

## Justfile
Used to run project-specific commands.
To see all commands available run:

```shell
just help
```

### Setup
Go to the root folder of the project and run the command below, it will create the environment and install all dependencies.

```shell
just setup
```

### Run the API locally
This command will run the server. You will be able to send a request to the API.

```shell
just start
```

To test the websocket access the URL below twice and send a message.
https://piehost.com/websocket-tester

In the WebSocket URL place
ws://localhost:8000/ws/connect

Now send messages


### Start server locally on Windows

```powershell
poetry env activate
poetry run fastapi dev src/main.py
```

## Cache
When the game is happening we will save all the actions on Redis for fast access.

[What is Redis](https://redis.io/)

[Server Cloud Redis](https://cloud.redis.io/#/databases)

## Actions
### Find Game Session
This action allows a player to join the matchmaking queue and either start a new game if an opponent is available, or wait for another player.

**How it works:**
- If another player is already waiting in the queue, a new game session is created and both players are matched.
- If no opponent is available, the player is added to the queue and waits for another player to join.

**Request Example**
```json
{
    "action": "find_game_session",
    "player_id": "b7e6a1c2-3d4f-4e5a-8b9c-123456789abc"
}
```
*Note: `player_id` should be a UUID string.*

**Possible Responses**

- **If a game session is created:**
    ```json
    {
        "status": "ready",
        "message": "Game has started",
        "action": "res_find_game_session",
        "data": {
            "game_id": "369a2125-fe46-45cb-86d1-816d0c96027d",
            "start_datetime": 1761393417,
            "end_datetime": 0,
            "players": "b7e6a1c2-3d4f-4e5a-8b9c-123456789abc",
            "current_turn": "b7e6a1c2-3d4f-4e5a-8b9c-123456789000",
            "status": "in_progress"
        }
    }
    ```

- **If waiting for another player:**
    ```json
    {
        "status": "waiting",
        "message": "Waiting for another player",
        "action": "res_find_game_session",
        "data": {
            "player_id": "b7e6a1c2-3d4f-4e5a-8b9c-123456789abc",
        },
    }
    ```


### Place Ships
This action allows a player to submit their ship placements for a game. The server will validate the ships and store them for the player.

**How it works:**
- The player sends a request with the game ID, their player ID, and a list of ships with their positions.
- The server validates the ship placements.
- If the placements are valid, the server stores them and responds with success.
- If the placements are invalid, an error message is returned.

**Request Example**
```json
{
  "action": "place_ships",
  "game_id": "e2c56db5-dffb-48d2-b060-d0f5a71096e0",
  "player_id": "b7e6a1c2-3d4f-4e5a-8b9c-123456789abc",
  "ships": [
    {"type": "battleship", "positions": ["A1", "A2", "A3", "A4"]},
    {"type": "destroyer", "positions": ["B1", "B2", "B3"]}
  ]
}
```

**Possible Responses**

- **Success:**
    ```json
    {
      "status": "OK",
      "message": "Ships placed for player b7e6a1c2-3d4f-4e5a-8b9c-123456789abc",
      "action": "resp_place_ships",
      "data": ""
    }
    ```

- **Invalid ship placement:**
    ```json
    {
      "status": "error",
      "message": "Invalid ship positions: ships overlap",
      "action": "resp_place_ships",
      "data": ""
    }
    ```


### Shoot
This action allows a player to fire at a target cell on the opponent's board.

**How it works:**
- The player sends a request with the game ID, their player ID, and the target cell (e.g., "B4").
- If there is no opponent or the opponent's board is not found, an error is returned.
- If the target cell matches a ship position, it is recorded as a hit. The response includes whether the ship was sunk.
- If the target cell does not match any ship, the response indicates a miss.

**Request Example**
```json
{
  "action": "shoot",
  "game_id": "e2c56db5-dffb-48d2-b060-d0f5a71096e0",
  "player_id": "b7e6a1c2-3d4f-4e5a-8b9c-123456789abc",
  "target": "B4"
}
```

**Possible Responses**

- **Hit (and possibly sunk):**
    ```json
    {
      "status": "OK",
      "message": "the shoot of the playerb7e6a1c2-3d4f-4e5a-8b9c-123456789abc hit the target:B4",
      "action": "resp_shoot",
      "data": {
        "status": "hit",
        "target": "B4",
        "ship_id": "ship_id_2",
        "sunk": false
      }
    }
    ```

- **Miss:**
    ```json
    {
      "status": "OK",
      "message": "the shoot of the playerb7e6a1c2-3d4f-4e5a-8b9c-123456789abc on target:B4",
      "action": "resp_shoot",
      "data": {
        "status": "miss",
        "target": "B4"
      }
    }
    ```

- **No opponent found:**
    ```json
    {
      "status": "error",
      "message": "No opponent found",
      "action": "resp_shoot",
      "data": ""
    }
    ```

- **Opponent board not found:**
    ```json
    {
      "status": "error",
      "message": "Opponentb7e6a1c2-3d4f-4e5a-8b9c-123456789abc board not found of game:e2c56db5-dffb-48d2-b060-d0f5a71096e0",
      "action": "resp_shoot",
      "data": ""
    }
    ```


### Get game info
Receive the information of the ships positions from a player based on game id

```json
{"action": "get_game_info","game_id": 1,"player_id": 1}
```






