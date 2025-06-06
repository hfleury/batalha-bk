from fastapi import FastAPI

from src.api.websocket_handler import router
from src.infra.logger import setup_logging

setup_logging()
app = FastAPI()
app.include_router(router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
