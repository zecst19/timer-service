import httpx

from app.core.celery_app import celery_app
from app.core.redis_client import get_redis
from app.core.config import settings

@celery_app.task(bind=True, name="fire_webhook", max_retries=3)
def fire_webhook(self, url: str, timer_id: str) -> dict:

    r = get_redis()
    fired_key = f"{settings.REDIS_PREFIX_FIRED}{timer_id}"
    
    acquired = r.set(fired_key, "1", nx=True, ex=settings.POST_FIRE_TTL)
    if not acquired:
        return {"status": "already_fired"}
    
    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.post(url, json={"timer_id": timer_id})
            response.raise_for_status()
        return {"status": "ok", "http_status": response.status_code}
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code < 500:
            return {"status": "client_error", "http_status": exc.response.status_code}
        r.delete(fired_key)
        raise self.retry(exc=exc)
    except (httpx.RequestError, httpx.TimeoutException) as exc:
        r.delete(fired_key)
        raise self.retry(exc)
