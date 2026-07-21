from collections.abc import AsyncIterator

import httpx
import pytest_asyncio
from httpx import ASGITransport
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker

from document_intelligence.db import make_engine
from document_intelligence.main import app


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
