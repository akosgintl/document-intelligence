"""Submission size/page-count limits (#25): a Submission over either configured limit is
rejected synchronously with `400` and a distinct `error.code`, before a Job is ever created —
driven entirely through the public HTTP API, per this repo's Testing Decisions.
"""

import pytest
from sqlalchemy import func, select
from test_walking_skeleton import AUTH_HEADERS, _n_page_pdf, _one_page_pdf

from document_intelligence.config import get_settings
from document_intelligence.db import Job


@pytest.fixture
def override_limits(monkeypatch):
    def _apply(**env: int) -> None:
        for key, value in env.items():
            monkeypatch.setenv(key, str(value))
        get_settings.cache_clear()

    yield _apply
    get_settings.cache_clear()


async def _job_count(db_session_factory) -> int:
    async with db_session_factory() as session:
        result = await session.execute(select(func.count()).select_from(Job))
        return result.scalar_one()


async def test_submission_within_limits_proceeds_normally(
    api_client, db_session_factory, override_limits
):
    override_limits(MAX_SUBMISSION_SIZE_BYTES=10_000, MAX_SUBMISSION_PAGES=5)

    response = await api_client.post(
        "/v1/submissions",
        headers=AUTH_HEADERS,
        files={"file": ("invoice.pdf", _n_page_pdf(2), "application/pdf")},
    )

    assert response.status_code == 202
    assert await _job_count(db_session_factory) == 1


async def test_submission_over_size_limit_is_rejected(api_client, db_session_factory, override_limits):
    override_limits(MAX_SUBMISSION_SIZE_BYTES=10)

    response = await api_client.post(
        "/v1/submissions",
        headers=AUTH_HEADERS,
        files={"file": ("invoice.pdf", _one_page_pdf(), "application/pdf")},
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "submission_too_large"
    assert await _job_count(db_session_factory) == 0


async def test_submission_over_page_count_limit_is_rejected(
    api_client, db_session_factory, override_limits
):
    override_limits(MAX_SUBMISSION_PAGES=2)

    response = await api_client.post(
        "/v1/submissions",
        headers=AUTH_HEADERS,
        files={"file": ("invoice.pdf", _n_page_pdf(3), "application/pdf")},
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "submission_too_many_pages"
    assert await _job_count(db_session_factory) == 0


def test_default_limits_are_50mb_and_200_pages():
    settings = get_settings()

    assert settings.max_submission_size_bytes == 50 * 1024 * 1024
    assert settings.max_submission_pages == 200
