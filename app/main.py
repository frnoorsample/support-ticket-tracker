from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()  # runs once when the server starts
    yield


app = FastAPI(title="Support Ticket Tracker", lifespan=lifespan)


@app.get("/health")
def health_check():
    return {"status": "ok"}