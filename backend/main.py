# backend/main.py
from fastapi import FastAPI
from .database import engine
from . import models

app = FastAPI()

@app.on_event("startup")
def on_startup():
    # Create all tables (no-op if they already exist)
    models.Base.metadata.create_all(bind=engine)


@app.get("/health")
def health():
    return {"status": "ok"}

