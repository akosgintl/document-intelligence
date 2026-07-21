from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from typing import Any

import aioboto3

from document_intelligence.config import get_settings

_session = aioboto3.Session()


@asynccontextmanager
async def get_s3_client() -> AsyncIterator[Any]:
    settings = get_settings()
    async with _session.client(
        "s3",
        endpoint_url=settings.s3_endpoint_url,
        aws_access_key_id=settings.s3_access_key,
        aws_secret_access_key=settings.s3_secret_key,
        region_name=settings.s3_region,
    ) as client:
        yield client
