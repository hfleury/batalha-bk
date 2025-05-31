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

## Cache
When the game is happening we will save all the actions on Redis for fast access.

[What is Redis](https://redis.io/)

[Server Cloud Redis](https://cloud.redis.io/#/databases)

## Actions
### Start the game
Receive the game id and the players
Example
```json
{"action":"start_game","game_id":1,"players":{"1":{"ship_id_1":["A1"],"ship_id_2":["B1","B2"],"ship_id_3":["C1","C2","C3"],"ship_id_4":["D1","D2","D3","D4"],"ship_id_5":["E1","E2","E3","E4","E5"]},"2":{"ship_id_1":["A5"],"ship_id_2":["B5","B6"],"ship_id_3":["C5","C6","C7"],"ship_id_4":["D5","D6","D7","D8"],"ship_id_5":["E5","E6","E7","E8","E9"]}}}
```

### Get game info
Receive the information of the ships positions from a player based on game id

```json
{"action": "get_game_info","game_id": 1,"player_id": 1}
```

### Player shoot
Receive the shoot a player did.

```json
{"action":"shoot","game_id":1,"player_id":1,"target":"B2"}
```

