"""Main application entry point for the Game server."""

import logging
import importlib.metadata
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import asyncpg  # type: ignore
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.v1 import auth_router
from src.api.v1.player_router import v1_router
from src.api.websocket_handler import router
from src.config import settings
from src.infrastructure.logger import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(appFast: FastAPI) -> AsyncGenerator[None, None]:
    """Manage the application's lifespan, handling startup and shutdown events."""
    logger.info("🚀 Starting up...")

    try:
        pool = await asyncpg.create_pool(dsn=settings.db.url)  # type: ignore
        appFast.state.db_pool = pool
        logger.info("🗄️ Connected to PostgreSQL")
    except Exception as e:
        logger.error(f"❌ Failed to connect to DB: {e}")
        raise

    yield  # Server runs here

    if hasattr(appFast.state, "db_pool"):
        await appFast.state.db_pool.close()
        logger.info("🛑 PostgreSQL connection closed")

try:
    APP_VERSION = importlib.metadata.version("batalha-naval")
except importlib.metadata.PackageNotFoundError:
    APP_VERSION = "0.0.0-local"

app = FastAPI(
    title=settings.app.title,
    version=APP_VERSION,
    debug=settings.app.debug,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your domain
    allow_credentials=True,
    allow_methods=["*"],  # Allows POST, OPTIONS, etc.
    allow_headers=["*"],
)

app.include_router(router)
app.include_router(v1_router)
app.include_router(auth_router.router)


@app.get("/")
def read_root() -> dict[str, str]:
    """Return a welcome message for the root endpoint."""
    return {"message": "Welcome to Batalha Naval", "docs": "/docs"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=settings.app.port,
        reload=settings.app.is_development or settings.app.is_local,
    )
