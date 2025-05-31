FROM python:3.13-slim

WORKDIR /app

# Install system dependencies and Poetry
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl \
    && pip install --upgrade pip \
    && curl -sSL https://install.python-poetry.org | python3 - \
    && rm -rf /var/lib/apt/lists/*

# Add Poetry to PATH
ENV PATH="/root/.local/bin:$PATH"

# Copy only poetry files first for caching
COPY pyproject.toml poetry.lock* ./

# Install dependencies (no virtualenv, install to system)
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --no-root

# Copy the rest of the project
COPY . .

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]