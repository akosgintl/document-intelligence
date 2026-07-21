from unittest.mock import AsyncMock

import pytest

from document_intelligence.health import (
    check_postgres,
    check_redis,
    check_storage,
    run_health_checks,
)


async def test_check_postgres_ok_when_query_succeeds():
    session = AsyncMock()
    session.execute = AsyncMock(return_value=None)

    result = await check_postgres(session)

    assert result.ok is True
    assert result.error is None
    session.execute.assert_awaited_once()


async def test_check_postgres_reports_error_on_failure():
    session = AsyncMock()
    session.execute = AsyncMock(side_effect=ConnectionError("connection refused"))

    result = await check_postgres(session)

    assert result.ok is False
    assert "connection refused" in result.error


async def test_check_redis_ok_when_ping_succeeds():
    client = AsyncMock()
    client.ping = AsyncMock(return_value=True)

    result = await check_redis(client)

    assert result.ok is True
    assert result.error is None


async def test_check_redis_reports_error_on_failure():
    client = AsyncMock()
    client.ping = AsyncMock(side_effect=ConnectionError("no route to host"))

    result = await check_redis(client)

    assert result.ok is False
    assert "no route to host" in result.error


async def test_check_storage_ok_when_bucket_reachable():
    client = AsyncMock()
    client.head_bucket = AsyncMock(return_value={})

    result = await check_storage(client, bucket="document-intelligence")

    assert result.ok is True
    assert result.error is None
    client.head_bucket.assert_awaited_once_with(Bucket="document-intelligence")


async def test_check_storage_reports_error_on_failure():
    client = AsyncMock()
    client.head_bucket = AsyncMock(side_effect=Exception("404 bucket not found"))

    result = await check_storage(client, bucket="document-intelligence")

    assert result.ok is False
    assert "bucket not found" in result.error


async def test_run_health_checks_aggregates_all_dependencies():
    session = AsyncMock()
    redis_client = AsyncMock()
    s3_client = AsyncMock()
    s3_client.head_bucket = AsyncMock(return_value={})

    results = await run_health_checks(
        session=session, redis_client=redis_client, s3_client=s3_client, bucket="bucket"
    )

    assert set(results.keys()) == {"postgres", "redis", "storage"}
    assert all(result.ok for result in results.values())


async def test_run_health_checks_reports_partial_failure():
    session = AsyncMock()
    redis_client = AsyncMock()
    redis_client.ping = AsyncMock(side_effect=ConnectionError("down"))
    s3_client = AsyncMock()
    s3_client.head_bucket = AsyncMock(return_value={})

    results = await run_health_checks(
        session=session, redis_client=redis_client, s3_client=s3_client, bucket="bucket"
    )

    assert results["postgres"].ok is True
    assert results["redis"].ok is False
    assert results["storage"].ok is True
