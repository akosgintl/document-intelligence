from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from arq import create_pool
from arq.connections import RedisSettings
from fastapi import Depends, FastAPI, Response
from sqlalchemy.ext.asyncio import AsyncSession

from document_intelligence.api.errors import ApiError, api_error_handler
from document_intelligence.api.jobs import router as jobs_router
from document_intelligence.api.submissions import router as submissions_router
from document_intelligence.config import get_settings
from document_intelligence.db import get_session
from document_intelligence.health import run_health_checks
from document_intelligence.redis_client import make_redis
from document_intelligence.storage import get_s3_client


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    app.state.arq_pool = await create_pool(RedisSettings.from_dsn(get_settings().redis_url))
    try:
        yield
    finally:
        await app.state.arq_pool.aclose()


app = FastAPI(title="document-intelligence", lifespan=lifespan)
app.add_exception_handler(ApiError, api_error_handler)
app.include_router(submissions_router)
app.include_router(jobs_router)


@app.get("/health")
async def health(response: Response, session: AsyncSession = Depends(get_session)) -> dict:
    settings = get_settings()

    async with make_redis() as redis_client, get_s3_client() as s3_client:
        results = await run_health_checks(
            session=session,
            redis_client=redis_client,
            s3_client=s3_client,
            bucket=settings.s3_bucket,
        )

    all_ok = all(result.ok for result in results.values())
    response.status_code = 200 if all_ok else 503

    return {
        "status": "ok" if all_ok else "degraded",
        "checks": {
            name: {"ok": result.ok, "error": result.error} for name, result in results.items()
        },
    }
