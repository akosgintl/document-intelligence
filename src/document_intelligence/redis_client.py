from redis.asyncio import Redis

from document_intelligence.config import get_settings


def make_redis() -> Redis:
    return Redis.from_url(get_settings().redis_url)
