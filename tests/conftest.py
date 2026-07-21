from collections.abc import AsyncIterator

import httpx
import pytest_asyncio
from httpx import ASGITransport
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker

from document_intelligence.db import make_engine
from document_intelligence.main import app
from document_intelligence.redis_client import make_redis


@pytest_asyncio.fixture(autouse=True)
async def flush_redis() -> AsyncIterator[None]:
    """Flush the `arq`/queue-related Redis DB after every test, mirroring the Postgres
    TRUNCATE in `db_session_factory` below: without this, keys left behind by `arq`
    accumulate across pytest invocations against the same shared Redis instance and
    eventually make unrelated tests fail (#30).

    Like `db_session_factory`, this points at the same local Redis the dev docker-compose
    stack uses (there's no separate test instance/DB index) — flushing it is this repo's
    established convention for local dev+test sharing infra, not a new risk.
    """
    try:
        yield
    finally:
        async with make_redis() as client:
            await client.flushdb()


@pytest_asyncio.fixture
async def db_session_factory() -> AsyncIterator[async_sessionmaker]:
    engine = make_engine()
    factory = async_sessionmaker(engine, expire_on_commit=False)
    try:
        yield factory
    finally:
        async with engine.begin() as conn:
            await conn.execute(
                text(
                    "TRUNCATE fields, pages, model_calls, documents, jobs, submissions "
                    "RESTART IDENTITY CASCADE"
                )
            )
        await engine.dispose()


@pytest_asyncio.fixture
async def api_client() -> AsyncIterator[httpx.AsyncClient]:
    async with app.router.lifespan_context(app):
        transport = ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            yield client
