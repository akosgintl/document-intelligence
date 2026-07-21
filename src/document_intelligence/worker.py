from contextlib import AsyncExitStack

import anthropic
from arq.connections import RedisSettings
from sqlalchemy.ext.asyncio import async_sessionmaker

from document_intelligence.config import get_settings
from document_intelligence.db import make_engine
from document_intelligence.model_provider.anthropic_provider import AnthropicModelProvider
from document_intelligence.pipeline import PipelineDeps
from document_intelligence.pipeline import process_document_extraction as _process_document_extraction
from document_intelligence.pipeline import process_job as _process_job
from document_intelligence.schema_registry import SchemaRegistry
from document_intelligence.storage import get_s3_client


async def startup(ctx: dict) -> None:
    settings = get_settings()

    exit_stack = AsyncExitStack()
    ctx["_exit_stack"] = exit_stack
    s3_client = await exit_stack.enter_async_context(get_s3_client())

    ctx["pipeline_deps"] = PipelineDeps(
        session_factory=async_sessionmaker(make_engine(), expire_on_commit=False),
        s3_client=s3_client,
        bucket=settings.s3_bucket,
        model_provider=AnthropicModelProvider(anthropic.AsyncAnthropic()),
        schema_registry=SchemaRegistry.load(settings.schema_registry_dir),
    )


async def shutdown(ctx: dict) -> None:
    exit_stack: AsyncExitStack | None = ctx.get("_exit_stack")
    if exit_stack is not None:
        await exit_stack.aclose()


async def ping(ctx: dict) -> str:
    """Placeholder task proving the worker can pick up and execute jobs."""
    return "pong"


async def process_job(ctx: dict, job_id: str) -> None:
    await _process_job(ctx["pipeline_deps"], job_id)


async def extract_document(ctx: dict, document_id: str) -> None:
    """Queued by `POST /v1/documents/{id}/review` (#26) once a classification resolution
    assigns a Document Type — runs Extraction the same way a freshly `classified` Document
    would get it from `process_job`, just outside that Document's original Job run."""
    await _process_document_extraction(ctx["pipeline_deps"], document_id)


class WorkerSettings:
    functions = [ping, process_job, extract_document]
    on_startup = startup
    on_shutdown = shutdown
    redis_settings = RedisSettings.from_dsn(get_settings().redis_url)
