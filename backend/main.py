# main.py
from fastapi import FastAPI, Depends
from sqlalchemy import inspect
from sqlalchemy.orm import Session
from database import engine, SessionLocal
import models


app = FastAPI()


@app.on_event("startup")
def on_startup():
    print("Creating tables (if they do not already exist)...")
    models.Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/tables")
def list_tables():
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    return {"tables": tables}


@app.get("/tables/{table_name}")
def describe_table(table_name: str):
    inspector = inspect(engine)
    if table_name not in inspector.get_table_names():
        return {"error": f"Table '{table_name}' does not exist."}

    columns_info = []
    for col in inspector.get_columns(table_name):
        columns_info.append({
            "name": col["name"],
            "type": str(col["type"]),
            "nullable": col["nullable"],
            "default": str(col["default"])
        })

    return {
        "table": table_name,
        "columns": columns_info
    }