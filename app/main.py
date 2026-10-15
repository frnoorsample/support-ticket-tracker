from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import init_db
from app.routers import auth


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()  
    yield


app = FastAPI(title="Support Ticket Tracker", lifespan=lifespan)

app.include_router(auth.router)


@app.get("/health")
def health_check():
    return {"status": "ok"}