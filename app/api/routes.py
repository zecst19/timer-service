import uuid
import math
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException

from app.api.schemas import TimerCreateRequest, TimerCreateResponse, TimerStatusResponse
from app.core.redis_client import get_redis
from app.core.config import settings
from app.tasks.webhook import fire_webhook

router = APIRouter(prefix="/timer", tags=["timers"])

def _fire_at_key(timer_id: str) -> str:
    return f"{settings.REDIS_PREFIX_FIRE_AT}{timer_id}"

@router.post("", response_model=TimerCreateResponse, status_code=201)
def create_timer(body: TimerCreateRequest):
    total = body.total_seconds()
    if total <= 0:
        raise HTTPException(
            status_code=400,
            detail="Timer duration must be greater than zero"
        )
    
    timer_id = str(uuid.uuid4())
    fire_at = datetime.now(timezone.utc) + timedelta(seconds=total)

    r = get_redis()
    r.set(_fire_at_key(timer_id), fire_at.isoformat(), ex=total + settings.POST_FIRE_TTL)
    
    fire_webhook.apply_async(
        kwargs={"url": str(body.url), "timer_id": timer_id},
        eta=fire_at,
    )

    return TimerCreateResponse(id=timer_id, time_left=total)


@router.get("/{timer_id}", response_model=TimerStatusResponse)
def get_timer(timer_id: str):
    r = get_redis()
    raw = r.get(_fire_at_key(timer_id))

    if raw is None:
        raise HTTPException(status_code=404, detail=f"Timer '{timer_id}' not found")
    
    fire_at = datetime.fromisoformat(raw)
    remaining = (fire_at - datetime.now(timezone.utc)).total_seconds()
    time_left = max(0, math.ceil(remaining))

    return TimerStatusResponse(id=timer_id, time_left=time_left)