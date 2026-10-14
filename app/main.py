from fastapi import FastAPI

app = FastAPI(title="Support Ticket Tracker")


@app.get("/health")
def health_check():
    return {"status": "ok"}