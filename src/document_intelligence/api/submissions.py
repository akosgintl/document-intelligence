import uuid
from typing import Annotated, Any

from arq import ArqRedis
from fastapi import APIRouter, Depends, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from document_intelligence.api.deps import get_arq_pool, require_api_key, s3_client_dependency
from document_intelligence.api.errors import (
    SubmissionTooLargeError,
    SubmissionTooManyPagesError,
    ValidationError,
)
from document_intelligence.api.dto import SubmissionAccepted
from document_intelligence.config import get_settings
from document_intelligence.db import Job, JobStatus, Submission, get_session
from document_intelligence.rendering import SUPPORTED_CONTENT_TYPES, RenderError, count_pages
from document_intelligence.storage import put_object

router = APIRouter(prefix="/v1/submissions", tags=["submissions"])


@router.post("", status_code=status.HTTP_202_ACCEPTED, response_model=SubmissionAccepted)
async def create_submission(
    file: UploadFile,
    _: Annotated[None, Depends(require_api_key)],
    session: Annotated[AsyncSession, Depends(get_session)],
    s3_client: Annotated[Any, Depends(s3_client_dependency)],
    arq_pool: Annotated[ArqRedis, Depends(get_arq_pool)],
) -> SubmissionAccepted:
    content_type = file.content_type
    if content_type not in SUPPORTED_CONTENT_TYPES:
        raise ValidationError(
            f"Unsupported content type '{content_type}'. Supported: "
            f"{', '.join(sorted(SUPPORTED_CONTENT_TYPES))}"
        )

    body = await file.read()
    if not body:
        raise ValidationError("Submission file is empty")

    settings = get_settings()
    if len(body) > settings.max_submission_size_bytes:
        raise SubmissionTooLargeError(
            f"Submission of {len(body)} bytes exceeds the "
            f"{settings.max_submission_size_bytes}-byte limit"
        )

    try:
        page_count = count_pages(body, content_type)
    except RenderError as exc:
        raise ValidationError(str(exc)) from exc
    if page_count > settings.max_submission_pages:
        raise SubmissionTooManyPagesError(
            f"Submission has {page_count} pages, exceeding the "
            f"{settings.max_submission_pages}-page limit"
        )

    submission_id = uuid.uuid4()
    storage_key = f"submissions/{submission_id}/original"
    await put_object(
        s3_client,
        bucket=settings.s3_bucket,
        key=storage_key,
        body=body,
        content_type=content_type,
    )

    submission = Submission(id=submission_id, content_type=content_type, storage_key=storage_key)
    job = Job(submission=submission, status=JobStatus.PENDING)
    session.add(submission)
    session.add(job)
    await session.commit()

    await arq_pool.enqueue_job("process_job", str(job.id))

    return SubmissionAccepted(job_id=job.id, status=job.status.value)
