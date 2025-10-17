"""Main application entry point for the Game server."""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI

from src.api.websocket_handler import router
from src.infra.logger import setup_logging
from src.core.config import settings

setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def log_startup_info(_app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Log application startup information.

    This function is a FastAPI lifespan event handler that logs key
    configuration details when the server starts.
    """
    logger.info(f"✅ Server starting in '{settings.app.environment}' mode")
    logger.info(
        f"📊 Database: {settings.db.host}:{settings.db.port} | DB={settings.db.database}"
    )
    logger.info(f"🧩 Redis: {settings.redis.host}:{settings.redis.port}")
    logger.info(f"🖨️ Logging level: {settings.log.log_level}")
    yield


app = FastAPI(
    title="Batalha Naval API",
    version="0.1.0",
    debug=settings.app.debug,
    lifespan=log_startup_info,
)
app.include_router(router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=settings.app.is_development or settings.app.is_local,
    )
