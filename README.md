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