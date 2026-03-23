"""
Config for the timer service
"""
import os

class Settings:
    REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

    REDIS_PREFIX_FIRE_AT: str = "timer:fire_at"
    REDIS_PREFIX_FIRED: str = "timer:fired"
    POST_FIRE_TTL: int = int(os.getenv("POST_FIRE_TTL", 7 * 24 * 3600))
    CELERY_TIMEZONE = "UTC"
    CELERY_BROKER_URL = REDIS_URL
    CELERY_RESULT_BACKEND = REDIS_URL
    CELERY_TASK_SERIALIZER = "json"
    CELERY_ACCEPT_CONTENT = ["json"]
    CELERY_RESULT_SERIALIZER = "json"
    CELERY_TASK_TRACK_STARTED = True
    CELERY_TASK_TIME_LIMIT = 300
    CELERY_TASK_SOFT_TIME_LIMIT = 250

settings = Settings()