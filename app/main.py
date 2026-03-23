"""
Timer service - FastAPI app entry point
"""
from fastapi import FastAPI

from app.api.routes import router as timer_router

app = FastAPI(
    title="Timer Service",
    version="1.0.0"
)

app.include_router(timer_router)