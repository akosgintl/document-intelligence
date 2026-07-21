import hmac
from collections.abc import AsyncIterator

from arq import ArqRedis
from fastapi import Header, Request

from document_intelligence.api.errors import AuthError
from document_intelligence.config import get_settings
from document_intelligence.storage import get_s3_client

_BEARER_PREFIX = "Bearer "


async def require_api_key(authorization: str | None = Header(default=None)) -> None:
    if authorization is None or not authorization.startswith(_BEARER_PREFIX):
        raise AuthError("Missing or malformed Authorization header")

    supplied = authorization.removeprefix(_BEARER_PREFIX)
    expected = get_settings().api_key
    if not hmac.compare_digest(supplied, expected):
        raise AuthError("Invalid API key")


async def s3_client_dependency() -> AsyncIterator[object]:
    async with get_s3_client() as client:
        yield client


def get_arq_pool(request: Request) -> ArqRedis:
    return request.app.state.arq_pool
