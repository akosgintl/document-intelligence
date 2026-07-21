import uuid
from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from document_intelligence.db import ModelCall, ModelCallType
from document_intelligence.model_provider.recording import ModelCallRecord


@dataclass(frozen=True)
class PersistingModelCallRecorder:
    """Persists every Model Provider call made while processing one Job.

    Registered in `current_model_call_recorder` for the duration of `process_job`
    (pipeline.py) — a Provider reports into it without knowing which Job it's serving,
    so any future call site (retries, new call types) is persisted automatically.

    Commits each call in its own short-lived session, independent of the Job's own
    transaction: a call must stay debuggable even if a *later* step in that same Job
    (e.g. an extraction validation failure) raises and rolls the Job's session back.
    """

    session_factory: async_sessionmaker[AsyncSession]
    job_id: uuid.UUID

    async def record(self, record: ModelCallRecord) -> None:
        async with self.session_factory() as session:
            session.add(
                ModelCall(
                    job_id=self.job_id,
                    call_type=ModelCallType(record.call_type),
                    prompt=record.prompt,
                    response=record.response,
                    input_tokens=record.input_tokens,
                    output_tokens=record.output_tokens,
                    latency_ms=record.latency_ms,
                )
            )
            await session.commit()


@dataclass(frozen=True)
class JobTokenUsage:
    input_tokens: int
    output_tokens: int


async def job_token_usage(session: AsyncSession, job_id: uuid.UUID) -> JobTokenUsage:
    """Total input/output tokens across every Model Provider call persisted for a Job."""
    result = await session.execute(
        select(
            func.coalesce(func.sum(ModelCall.input_tokens), 0),
            func.coalesce(func.sum(ModelCall.output_tokens), 0),
        ).where(ModelCall.job_id == job_id)
    )
    input_tokens, output_tokens = result.one()
    return JobTokenUsage(input_tokens=input_tokens, output_tokens=output_tokens)
