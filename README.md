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
- Players can optionaly specify a `faction` (Marines, Pirates, Winders). Default is Marines.

**Request Example**
```json
{
    "action": "find_game_session",
    "player_id": "b7e6a1c2-3d4f-4e5a-8b9c-123456789abc",
    "faction": "Marines"
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
- If the placements are valid, the server stores them.
- If both players have placed their ships, the game starts (status `battle_start`).

**Request Example**
```json
{
  "action": "place_ships",
  "game_id": "e2c56db5-dffb-48d2-b060-d0f5a71096e0",
  "player_id": "b7e6a1c2-3d4f-4e5a-8b9c-123456789abc",
  "ships": [
    {"type": "Battleship", "positions": ["A1", "A2", "A3", "A4"]},
    {"type": "Destroyer", "positions": ["B1", "B2", "B3"]}
  ]
}
```

**Possible Responses**

- **Ships placed (waiting for opponent):**
    ```json
    {
      "status": "shipsPlaced",
      "message": "Ships placed for player b7e6a1c2-3d4f-4e5a-8b9c-123456789abc",
      "action": "place_ship_response",
      "data": {
          "game_id": "e2c56db5-dffb-48d2-b060-d0f5a71096e0",
          "player_id": "b7e6a1c2-3d4f-4e5a-8b9c-123456789abc"
      }
    }
    ```

- **Battle Start (Both players ready):**
    ```json
    {
        "status": "battle_start",
        "message": "Ships placed. Battle starting!",
        "action": "place_ship_response",
        "data": {
            "game_id": "e2c56db5-dffb-48d2-b060-d0f5a71096e0",
            "player_id": "b7e6a1c2-3d4f-4e5a-8b9c-123456789abc",
            "firstTurn": "b7e6a1c2-3d4f-4e5a-8b9c-123456789abc"
        }
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
- The player sends a request with the game ID, their player ID, the target cell (e.g., "B4"), and the `ship_type` used to shoot.
- Different ships (based on Faction) have different shooting strategies and fuel costs.
- If the player has enough fuel, the shot is processed.
- The outcome (hit, miss, sink) is returned, and fuel is deducted.

**Request Example**
```json
{
  "action": "shoot",
  "game_id": "e2c56db5-dffb-48d2-b060-d0f5a71096e0",
  "player_id": "b7e6a1c2-3d4f-4e5a-8b9c-123456789abc",
  "target": "B4",
  "ship_type": "Battleship"
}
```

**Possible Responses**

- **Hit (and possibly sunk):**
    ```json
    {
      "status": "OK",
      "message": "the shoot of the player ... hit the target:B4",
      "action": "shoot_result",
      "data": {
        "result": "hit",
        "cell": "B4",
        "ship_id": "ship_id_2",
        "sunk": false,
        "player_turn": "opponent_uuid"
      }
    }
    ```

- **Miss:**
    ```json
    {
      "status": "OK",
      "message": "the shoot of the player ... on target:B4",
      "action": "shoot_result",
      "data": {
        "result": "miss",
        "cell": "B4",
        "player_turn": "opponent_uuid"
      }
    }
    ```

- **Not enough fuel:**
    ```json
    {
      "status": "error",
      "message": "Not enough fuel. Need 10, have 5",
      "action": "shoot_result",
      "data": ""
    }
    ```

- **No opponent found:**
    ```json
    {
      "status": "error",
      "message": "No opponent found",
      "action": "shoot_result",
      "data": ""
    }
    ```

- **Opponent board not found:**
    ```json
    {
      "status": "error",
      "message": "Opponent ... board not found ...",
      "action": "shoot_result",
      "data": ""
    }
    ```

### Pass Turn
Allows a player to pass their turn to the opponent.

**Request Example**
```json
{
  "action": "pass_turn",
  "game_id": "e2c56db5-dffb-48d2-b060-d0f5a71096e0",
  "player_id": "b7e6a1c2-3d4f-4e5a-8b9c-123456789abc"
}
```

**Response**
```json
{
    "status": "ok",
    "message": "Turn passed successfully",
    "action": "confirm_pass_turn",
    "data": {
        "currentTurn": "opponent_uuid",
        "game_id": "e2c56db5-dffb-48d2-b060-d0f5a71096e0"
    }
}
```


### Get game info
Receive the information of the ships positions from a player based on game id

```json
{"action": "get_game_info","game_id": 1,"player_id": 1}
```






