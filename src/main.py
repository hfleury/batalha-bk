"""Main application entry point for the Game server."""

import asyncpg
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI

from src.api.v1.player_router import v1_router
from src.api.websocket_handler import router
from src.infra.logger import setup_logging
from src.core.config import settings

setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("🚀 Starting up...")

    try:
        pool = await asyncpg.create_pool(dsn=settings.db.url)
        app.state.db_pool = pool
        logger.info("🗄️ Connected to PostgreSQL")
    except Exception as e:
        logger.error(f"❌ Failed to connect to DB: {e}")
        raise

    yield  # Server runs here

    if hasattr(app.state, "db_pool"):
        await app.state.db_pool.close()
        logger.info("🛑 PostgreSQL connection closed")


app = FastAPI(
    title="Batalha Naval API",
    version="0.1.0",
    debug=settings.app.debug,
    lifespan=lifespan,
)
app.include_router(router)
app.include_router(v1_router)


@app.get("/")
def read_root() -> dict[str, str]:
    return {"message": "Welcome to Batalha Naval", "docs": "/docs"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=settings.app.is_development or settings.app.is_local,
    )
