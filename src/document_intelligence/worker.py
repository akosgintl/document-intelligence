from arq.connections import RedisSettings

from document_intelligence.config import get_settings


async def startup(ctx: dict) -> None:
    pass


async def shutdown(ctx: dict) -> None:
    pass


async def ping(ctx: dict) -> str:
    """Placeholder task proving the worker can pick up and execute jobs."""
    return "pong"


class WorkerSettings:
    functions = [ping]
    on_startup = startup
    on_shutdown = shutdown
    redis_settings = RedisSettings.from_dsn(get_settings().redis_url)
