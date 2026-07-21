from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from typing import Any

import aioboto3
from botocore.config import Config

from document_intelligence.config import get_settings

_session = aioboto3.Session()

# MinIO (and most self-hosted S3-compatible stores) don't support virtual-hosted-style
# addressing (bucket.host/key) — force path-style (host/bucket/key), boto3's default only
# for real AWS endpoints.
_CLIENT_CONFIG = Config(s3={"addressing_style": "path"})


@asynccontextmanager
async def get_s3_client() -> AsyncIterator[Any]:
    settings = get_settings()
    async with _session.client(
        "s3",
        endpoint_url=settings.s3_endpoint_url,
        aws_access_key_id=settings.s3_access_key,
        aws_secret_access_key=settings.s3_secret_key,
        region_name=settings.s3_region,
        config=_CLIENT_CONFIG,
    ) as client:
        yield client


async def put_object(client: Any, *, bucket: str, key: str, body: bytes, content_type: str) -> None:
    await client.put_object(Bucket=bucket, Key=key, Body=body, ContentType=content_type)


async def get_object_bytes(client: Any, *, bucket: str, key: str) -> bytes:
    response = await client.get_object(Bucket=bucket, Key=key)
    async with response["Body"] as stream:
        return await stream.read()
