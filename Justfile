## Show this help message
help:
    @echo "Usage: just [command]"
    @echo ""
    @echo "Available commands:"
    @just --list | awk -F '##' '{printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}' | grep -v '^help'

## Set up the development environment
setup:
    chmod +x ./scripts/setup.sh && ./scripts/setup.sh

## Start the FastAPI server
start:
    poetry run fastapi dev src/main.py

## Run tests
test:
    poetry run coverage run -p -m pytest tests/
    poetry run coverage combine
    poetry run coverage report -m


## Format code with Black and isort
format:
    poetry run black . && poetry run isort .

## Lint code with Flake8 and mypy
lint:
    poetry run flake8 src/ tests/
    poetry run mypy src/
    poetry run pylint --rcfile=.pylintrc src/ tests/

test1:
    fastapi dev main.py
