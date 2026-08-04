---
type: wiki entrypoint
title: Document Intelligence Wiki
description: A source-grounded guide to the document intelligence API, worker pipeline, schemas, data, and operations.
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
- [Synthetic fixtures and golden evaluation](quality/fixtures-and-evaluation.md) — co-derived test artifacts and paid real-provider accuracy reporting.
- [Runtime configuration and validation](operations/runtime-and-validation.md) — Compose, settings, health, secrets boundaries, and test commands.

## Start from an engineering intent

| Change or question | Read first | Owning source surfaces | Focused check |
| --- | --- | --- | --- |
| Add/change endpoint, auth, DTO, or error | [HTTP API](api/http-api.md) | `api/*.py`, `main.py` | relevant route test; `test_walking_skeleton.py` for full path |
| Change submission file limits or admission order | [HTTP API](api/http-api.md) | `api/submissions.py`, `rendering.py`, `storage.py` | `tests/test_submission_limits.py` |
| Change grouping/classification/extraction behavior | [Processing pipeline](pipeline/processing.md) | `pipeline.py`, `grouping.py`, `rendering.py` | `test_multi_page_splitting.py`, `test_extraction_validation.py` |
| Change review or retry/crash behavior | [Review and recovery](pipeline/review-and-recovery.md) | `api/documents.py`, `pipeline.py`, `worker.py` | `test_confidence_review.py`, recovery tests |
| Integrate a model vendor or retry policy | [Model provider](model-provider/adapter-and-retries.md) | `model_provider/`, `worker.py` | provider contract/retry tests |
| Add a document type or evolve an extraction schema | [Schema registry](schemas/registry-and-authoring.md) | `schemas/`, `schema_registry/` | `test_schema_registry.py`, fixture tests |
| Change persistent data/migrations | [Persistence](data/persistence.md) | `db/models.py`, `migrations/` | migration plus lifecycle tests |
| Add fixture/golden example or investigate accuracy | [Fixtures and evaluation](quality/fixtures-and-evaluation.md) | `fixtures/`, `eval/` | `test_fixture_renderer.py`; optionally `eval/run_eval.py` |
| Start/debug deployment dependencies | [Runtime and validation](operations/runtime-and-validation.md) | `docker-compose.yml`, `config.py`, `health.py` | `/health`, focused suite |

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
