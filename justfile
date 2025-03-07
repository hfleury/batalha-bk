setup:
    chmod +x ./scripts/setup.sh && ./scripts/setup.sh

start:
    poetry run uvicorn main:app --reload --port 8000

test:
    poetry run pytest

format:
    poetry run black . && poetry run isort .

lint:
    poetry run flake8 && poetry run mypy .