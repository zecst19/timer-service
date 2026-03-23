"""
Celery instance and config
"""
from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "timer_service",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.update( # type: ignore
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_track_started=True,
    timezone=settings.CELERY_TIMEZONE,
    enable_utc=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)