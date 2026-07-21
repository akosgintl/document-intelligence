import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from document_intelligence.api.deps import require_api_key
from document_intelligence.api.dto import JobResult
from document_intelligence.api.errors import NotFoundError
from document_intelligence.db import Document, Job, get_session

router = APIRouter(prefix="/v1/jobs", tags=["jobs"])


@router.get("/{job_id}", response_model=JobResult)
async def get_job(
    job_id: uuid.UUID,
    _: Annotated[None, Depends(require_api_key)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> JobResult:
    result = await session.execute(
        select(Job)
        .where(Job.id == job_id)
        .options(selectinload(Job.documents).selectinload(Document.fields))
    )
    job = result.scalar_one_or_none()
    if job is None:
        raise NotFoundError(f"No Job with id {job_id}")

    return JobResult.from_job(job)
