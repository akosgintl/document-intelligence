"""Test-only helpers for driving the real `arq` queue/worker machinery against a
`FakeModelProvider`, per this repo's Testing Decisions (only the Model Provider is faked)."""

from arq.connections import RedisSettings
from arq.worker import Worker, func

from document_intelligence import pipeline
from document_intelligence.pipeline import PipelineDeps


async def run_worker_burst(*, redis_url: str, deps: PipelineDeps) -> None:
    """Run a real `arq` worker in burst mode: process every currently-queued Job, then exit."""

    async def process_job(ctx: dict, job_id: str) -> None:
        await pipeline.process_job(deps, job_id)

    async def extract_document(ctx: dict, document_id: str) -> None:
        await pipeline.process_document_extraction(deps, document_id)

    worker = Worker(
        functions=[
            func(process_job, name="process_job"),
            func(extract_document, name="extract_document"),
        ],
        redis_settings=RedisSettings.from_dsn(redis_url),
        burst=True,
        poll_delay=0.1,
        handle_signals=False,
    )
    try:
        await worker.async_run()
    finally:
        await worker.close()
