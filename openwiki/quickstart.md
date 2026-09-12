---
type: wiki entrypoint
title: Document Intelligence Wiki
description: A source-grounded guide to the document intelligence API, worker pipeline, schemas, data, quality workflows, and operations.
tags: [documentation, navigation]
---

# Document Intelligence Wiki

This repository is a schema-based document classification and extraction system. A FastAPI service accepts supported document files; an arq worker renders pages, classifies logical documents, extracts schema-defined fields through a model-provider interface, and stores results for polling and review. PostgreSQL owns lifecycle/results, Redis delivers work, and MinIO/S3 holds bytes.

## Map of the system

- [System architecture](architecture/overview.md) — service boundaries, composition roots, and the end-to-end runtime map.
- [HTTP API and submission admission](api/http-api.md) — endpoint contracts, bearer authentication, validation/errors, and the S3 → PostgreSQL → arq handoff.
- [Processing pipeline](pipeline/processing.md) — rendering, two-phase classification, grouping, extraction, confidence, validation, and idempotency.
- [Review, failure, and recovery](pipeline/review-and-recovery.md) — human resolution, retries, terminal states, and stuck-job reconciliation.
- [Model provider adapter and retry policy](model-provider/adapter-and-retries.md) — vendor-neutral protocol, Anthropic tools, retries, and model-call recording.
- [Persistence, storage, and migrations](data/persistence.md) — durable entities, object keys, relationships, and migration change surface.
- [Schema registry and document type authoring](schemas/registry-and-authoring.md) — schema directory contract, thresholds/versions, and current document types.
- [Synthetic fixtures and golden evaluation](quality/fixtures-and-evaluation.md) — co-derived test artifacts, privacy-preserving identifier helpers, renderer fidelity limits, and paid real-provider accuracy reporting.
- [Manual reference capture](quality/manual-reference-capture.md) — the human Számlázz.hu demófiók wizard for collecting invoice layout evidence outside the repository.
- [Runtime configuration and validation](operations/runtime-and-validation.md) — Compose, settings, health, secrets boundaries, and test commands.
- [OpenWiki maintenance workflow](operations/openwiki-maintenance.md) — scheduled/manual documentation update automation, provider settings, workflow guard, and PR publication.

## Start from an engineering intent

| Change area or user intent | Relevant wiki page | Exact source entry points | Important symbols or types | Focused tests | Minimal validation command |
| --- | --- | --- | --- | --- | --- |
| Add/change endpoint, auth, DTO, or error | [HTTP API](api/http-api.md) | `src/document_intelligence/main.py`, `src/document_intelligence/api/` | `require_api_key`, `ApiError`, `SubmissionAccepted`, `JobResult`, `DocumentResult` | focused route test; `tests/test_walking_skeleton.py` for full path | `uv run pytest tests/test_walking_skeleton.py` |
| Change submission file limits or admission order | [HTTP API](api/http-api.md) | `src/document_intelligence/api/submissions.py`, `src/document_intelligence/rendering.py`, `src/document_intelligence/storage.py` | `create_submission`, `count_pages`, `put_object`, `Settings.max_submission_size_bytes`, `Settings.max_submission_pages` | `tests/test_submission_limits.py` | `uv run pytest tests/test_submission_limits.py` |
| Change grouping, classification, extraction, or confidence gates | [Processing pipeline](pipeline/processing.md) | `src/document_intelligence/pipeline.py`, `src/document_intelligence/grouping.py`, `src/document_intelligence/rendering.py` | `process_job`, `PipelineDeps`, `group_pages_into_documents`, `extraction_validation_errors`, `DocumentStatus` | `tests/test_multi_page_splitting.py`, `tests/test_extraction_validation.py`, `tests/test_confidence_review.py` | `uv run pytest tests/test_multi_page_splitting.py tests/test_extraction_validation.py tests/test_confidence_review.py` |
| Change review transitions, retries, idempotency, or crash recovery | [Review and recovery](pipeline/review-and-recovery.md) | `src/document_intelligence/api/documents.py`, `src/document_intelligence/pipeline.py`, `src/document_intelligence/worker.py` | `review_document`, `extract_document`, `mark_job_failed`, `reconcile_stuck_jobs`, `_MAX_JOB_ATTEMPTS` | `tests/test_confidence_review.py`, `tests/test_job_failure.py`, `tests/test_pipeline_idempotency.py`, `tests/test_stuck_job_reconciliation.py` | `uv run pytest tests/test_confidence_review.py tests/test_job_failure.py tests/test_pipeline_idempotency.py tests/test_stuck_job_reconciliation.py` |
| Integrate a model vendor, tool schema, retry policy, or call recording | [Model provider](model-provider/adapter-and-retries.md) | `src/document_intelligence/model_provider/`, `src/document_intelligence/worker.py` | `ModelProvider`, `AnthropicModelProvider`, `RetryingModelProvider`, `TransientProviderError`, `PersistingModelCallRecorder` | `tests/test_model_provider_contract.py`, `tests/test_model_provider_anthropic.py`, `tests/test_transient_retry.py`, `tests/test_observability.py` | `uv run pytest tests/test_model_provider_contract.py tests/test_model_provider_anthropic.py tests/test_transient_retry.py tests/test_observability.py` |
| Add a document type or evolve an extraction schema | [Schema registry](schemas/registry-and-authoring.md) | `schemas/`, `src/document_intelligence/schema_registry/registry.py` | `SchemaRegistry`, `RegisteredDocumentType`, `DocumentTypeSchema`, `confidence_threshold` | `tests/test_schema_registry.py`, `tests/test_model_provider_anthropic.py`, `tests/test_extraction_validation.py` | `uv run pytest tests/test_schema_registry.py tests/test_model_provider_anthropic.py tests/test_extraction_validation.py` |
| Change persistent data, object keys, or migrations | [Persistence](data/persistence.md) | `src/document_intelligence/db/models.py`, `src/document_intelligence/db/session.py`, `migrations/`, `src/document_intelligence/storage.py` | `Submission`, `Job`, `Document`, `Page`, `Field`, `ModelCall`, `Base.metadata` | lifecycle tests plus migration smoke | `uv run alembic upgrade head` |
| Add fixture/golden example, MRZ identifier, or investigate accuracy | [Fixtures and evaluation](quality/fixtures-and-evaluation.md) | `fixtures/catalogue.py`, `fixtures/generate.py`, `fixtures/identifiers.py`, `fixtures/render.py`, `eval/run_eval.py` | `EXAMPLES`, `Example`, `Submission`, `Row`, `Table`, `Mrz`, `AmbiguousTransliteration`, `FixtureDoesNotFit` | `tests/test_fixture_renderer.py`; paid eval is conditional | `uv run pytest tests/test_fixture_renderer.py` |
| Collect a Számlázz.hu demo invoice PDF as external layout evidence | [Manual reference capture](quality/manual-reference-capture.md) | `scripts/issue_demo_invoice_wizard.sh` | `ENV_FILE`, `TOTAL_STAGES`, issuer gate, PDF gate, `PDF_PATH`, `SURPRISES` | Bash syntax check; manual browser run is conditional | `bash -n scripts/issue_demo_invoice_wizard.sh` |
| Start/debug deployment dependencies or settings | [Runtime and validation](operations/runtime-and-validation.md) | `docker-compose.yml`, `src/document_intelligence/config.py`, `src/document_intelligence/health.py`, `src/document_intelligence/worker.py` | `Settings`, `get_settings`, `run_health_checks`, `WorkerSettings` | dependency health plus relevant focused suite | `curl http://localhost:8000/health` |
| Change scheduled OpenWiki documentation automation | [OpenWiki maintenance workflow](operations/openwiki-maintenance.md) | `.github/workflows/openwiki-update.yml` | `OpenWiki Update`, `OPENWIKI_PROVIDER`, `OPENAI_API_KEY`, `OPENWIKI_MODEL_ID`, `Restore protected workflow file` | GitHub Actions workflow run | `gh workflow run openwiki-update.yml` |

## Concepts to keep distinct

A **Submission** is an uploaded file; a **Job** is its asynchronous processing lifecycle; a **Document** is a logical contiguous page group within that submission; a **Page** is a stored rendered image; and **Fields** are schema-validated extracted values. Job failure is not the same as a document-level extraction failure or a review-needed result. The [processing](pipeline/processing.md) page defines these boundaries precisely.

The schema registry provides both model guidance and validation. Latest schemas are classification candidates, but each classified document binds an explicit version for extraction/review. Model output confidence is a provider self-report compared with a per-document-type threshold. See [schema registry](schemas/registry-and-authoring.md) and [model provider](model-provider/adapter-and-retries.md).

## First local path

1. Start dependencies and services with `docker compose up -d` after configuring the required worker credential.
2. Check `curl http://localhost:8000/health`.
3. Submit/poll the generated sample with `uv run python scripts/manual_test.py`.
4. Use `uv run pytest` for deterministic validation.

For configuration source/caching and secret boundaries, do not rely on this summary; read [runtime configuration and validation](operations/runtime-and-validation.md).

## Backlog

No substantial inspected repository area is deferred. The golden evaluation README notes that identity-document golden examples are planned, but this is product coverage work anchored at `eval/README.md`, not undocumented repository behavior.
