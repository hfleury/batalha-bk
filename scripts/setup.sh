#!/bin/bash
# Setup virtual environment and install dependencies

# Check if Poetry is installed
if ! command -v poetry &> /dev/null
then
    echo "Poetry could not be found. Please install Poetry first."
    exit
fi

# Create virtual environment named "batalha-naval"
poetry config virtualenvs.in-project true
poetry config virtualenvs.path ".venv/batalha-naval"

# Install dependencies
poetry install --no-root

echo "✅ Environment 'batalha-naval' created and dependencies installed!"
echo "Activate with: poetry shell"