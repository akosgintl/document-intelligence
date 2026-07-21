import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


@dataclass
class CheckResult:
    ok: bool
    error: str | None = None


async def _run_check(probe: Callable[[], Awaitable[Any]]) -> CheckResult:
    try:
        await probe()
        return CheckResult(ok=True)
    except Exception as exc:
        return CheckResult(ok=False, error=str(exc))


async def check_postgres(session: AsyncSession) -> CheckResult:
    return await _run_check(lambda: session.execute(text("SELECT 1")))


async def check_redis(client: Any) -> CheckResult:
    return await _run_check(client.ping)


async def check_storage(client: Any, bucket: str) -> CheckResult:
    return await _run_check(lambda: client.head_bucket(Bucket=bucket))


async def run_health_checks(
    *, session: AsyncSession, redis_client: Any, s3_client: Any, bucket: str
) -> dict[str, CheckResult]:
    postgres, redis_, storage = await asyncio.gather(
        check_postgres(session),
        check_redis(redis_client),
        check_storage(s3_client, bucket),
    )
    return {"postgres": postgres, "redis": redis_, "storage": storage}
