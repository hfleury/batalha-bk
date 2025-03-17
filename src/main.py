from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def read_root() -> dict:
    """Root endpoint

    Returns:
        dict: Message
    """
    return {"message": "Naval Battle API"}
