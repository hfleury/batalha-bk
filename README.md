# batalha-bk
The backend for the game Naval Battle, version 1 is a monolithic using Python and FastAPI

## Start
To start have installed the JustFile program, [here is the link](https://github.com/casey/just)

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

If you access the address below you will see the JSON for the default URL

http://localhost:8000

You can use Swagger to see and test each endpoint and its documentation.

http://127.0.0.1:8000/docs