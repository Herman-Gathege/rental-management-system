from fastapi import FastAPI
from app.db.session import engine
from app.db.base import Base

app = FastAPI(title="Rental Management API")



@app.get("/health")
def health_check():
    return {"status": "ok"}