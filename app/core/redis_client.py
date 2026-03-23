import redis

from app.core.config import settings

_pool = redis.ConnectionPool.from_url(settings.REDIS_URL, decode_responses=True) # pyright: ignore[reportUnknownMemberType]

def get_redis() -> redis.Redis:
    return redis.Redis(connection_pool=_pool)