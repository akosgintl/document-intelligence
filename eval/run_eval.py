#!/usr/bin/env python3
"""Golden-dataset evaluation harness (#29).

Runs every golden example under `eval/golden/` through the real pipeline — the real
`AnthropicModelProvider` (wrapped in the same `RetryingModelProvider` production uses), never
`FakeModelProvider` — and reports classification/extraction accuracy broken down per Document
Type and per Field. A standalone script, not a pytest suite: a probabilistic Model Provider
makes per-example pass/fail assertions flaky, so this reports accuracy instead of asserting it.

Requires:
- Postgres, Redis, and MinIO reachable per `.env` (`docker compose up -d postgres redis minio
  minio-createbucket`), with migrations applied (`uv run alembic upgrade head`).
- A real `ANTHROPIC_API_KEY` in `.env` — this makes real, billed Model Provider calls.

Usage:
    uv run python eval/run_eval.py [--golden-dir eval/golden] [--model MODEL_NAME]

See eval/README.md for how to add a new golden example.
"""

import argparse
import asyncio
import json
import mimetypes
import sys
import uuid
from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import anthropic
from dotenv import load_dotenv
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.orm import selectinload

from document_intelligence.config import get_settings
from document_intelligence.db import Document, Job, JobStatus, Submission, make_engine
from document_intelligence.model_provider.anthropic_provider import AnthropicModelProvider
from document_intelligence.model_provider.retry import RetryingModelProvider
from document_intelligence.pipeline import PipelineDeps, process_job
from document_intelligence.rendering import SUPPORTED_CONTENT_TYPES
from document_intelligence.schema_registry import SchemaRegistry
from document_intelligence.storage import get_s3_client, put_object

_FLOAT_TOLERANCE = 0.01


@dataclass(frozen=True)
class GoldenExample:
    """One golden example: a Submission file paired with its known-correct result."""

    name: str
    submission_path: Path
    expected_document_type: str | None
    expected_schema_version: int | None
    expected_fields: dict[str, Any]


@dataclass(frozen=True)
class FieldOutcome:
    name: str
    expected: Any
    actual: Any
    correct: bool


@dataclass(frozen=True)
class ExampleOutcome:
    example: GoldenExample
    document_count: int
    actual_document_type: str | None
    actual_schema_version: int | None
    actual_status: str | None
    classification_correct: bool
    field_outcomes: tuple[FieldOutcome, ...]

    @property
    def fully_correct(self) -> bool:
        return (
            self.document_count == 1
            and self.classification_correct
            and all(f.correct for f in self.field_outcomes)
        )


def _content_type_of(path: Path) -> str | None:
    return mimetypes.guess_type(path.name)[0]


def load_golden_examples(golden_dir: Path) -> list[GoldenExample]:
    examples = []
    for expected_path in sorted(golden_dir.rglob("expected.json")):
        directory = expected_path.parent
        candidates = sorted(
            path
            for path in directory.glob("submission.*")
            if _content_type_of(path) in SUPPORTED_CONTENT_TYPES
        )
        if not candidates:
            raise SystemExit(f"{directory}: no submission.<ext> file found alongside expected.json")
        if len(candidates) > 1:
            raise SystemExit(f"{directory}: multiple submission.* files found, expected exactly one")

        expected = json.loads(expected_path.read_text())
        examples.append(
            GoldenExample(
                name=str(directory.relative_to(golden_dir)),
                submission_path=candidates[0],
                expected_document_type=expected.get("document_type"),
                expected_schema_version=expected.get("schema_version"),
                expected_fields=expected.get("fields") or {},
            )
        )
    return examples


def _is_number(value: Any) -> bool:
    return isinstance(value, int | float) and not isinstance(value, bool)


def _values_match(expected: Any, actual: Any) -> bool:
    if _is_number(expected) and _is_number(actual):
        return abs(float(expected) - float(actual)) <= _FLOAT_TOLERANCE
    return bool(expected == actual)


async def _run_example(deps: PipelineDeps, example: GoldenExample) -> Job:
    """Submit one golden example's file and run it through the real pipeline end to end,
    exactly like `POST /v1/submissions` does (minus the `arq` queue hop — `process_job` is
    called directly, since this harness doesn't need a running worker)."""
    content_type = _content_type_of(example.submission_path)
    assert content_type in SUPPORTED_CONTENT_TYPES, f"unsupported content type: {content_type}"
    body = example.submission_path.read_bytes()

    submission_id = uuid.uuid4()
    storage_key = f"eval/{example.name}/{submission_id}/original"
    await put_object(
        deps.s3_client, bucket=deps.bucket, key=storage_key, body=body, content_type=content_type
    )

    async with deps.session_factory() as session:
        submission = Submission(id=submission_id, content_type=content_type, storage_key=storage_key)
        job = Job(submission=submission, status=JobStatus.PENDING)
        session.add(submission)
        session.add(job)
        await session.commit()
        job_id = job.id

    await process_job(deps, str(job_id))

    async with deps.session_factory() as session:
        result = await session.execute(
            select(Job)
            .where(Job.id == job_id)
            .options(selectinload(Job.documents).selectinload(Document.fields))
        )
        return result.scalar_one()


def _evaluate(example: GoldenExample, job: Job) -> ExampleOutcome:
    documents = job.documents
    if len(documents) != 1:
        return ExampleOutcome(
            example=example,
            document_count=len(documents),
            actual_document_type=None,
            actual_schema_version=None,
            actual_status=None,
            classification_correct=False,
            field_outcomes=tuple(
                FieldOutcome(name, expected_value, None, False)
                for name, expected_value in example.expected_fields.items()
            ),
        )

    document = documents[0]
    classification_correct = (
        document.document_type_name == example.expected_document_type
        and document.schema_version == example.expected_schema_version
    )
    actual_fields = {f.name: f.value for f in document.fields}
    field_outcomes = tuple(
        FieldOutcome(
            name=name,
            expected=expected_value,
            actual=actual_fields.get(name),
            correct=name in actual_fields and _values_match(expected_value, actual_fields[name]),
        )
        for name, expected_value in example.expected_fields.items()
    )
    return ExampleOutcome(
        example=example,
        document_count=1,
        actual_document_type=document.document_type_name,
        actual_schema_version=document.schema_version,
        actual_status=document.status.value,
        classification_correct=classification_correct,
        field_outcomes=field_outcomes,
    )


def _pct(correct: int, total: int) -> str:
    return "n/a" if total == 0 else f"{100 * correct / total:.1f}%"


def _print_accuracy_row(label: str, results: Sequence[bool]) -> None:
    correct = sum(results)
    total = len(results)
    print(f"  {label:<24} {correct}/{total}  ({_pct(correct, total)})")


def print_report(outcomes: Sequence[ExampleOutcome]) -> None:
    print(f"\n{len(outcomes)} golden example(s) evaluated\n")

    for outcome in outcomes:
        marker = "PASS" if outcome.fully_correct else "FAIL"
        print(f"[{marker}] {outcome.example.name}")
        if outcome.document_count != 1:
            print(f"    structural mismatch: expected 1 Document, got {outcome.document_count}")
            continue
        if not outcome.classification_correct:
            print(
                f"    classification: expected {outcome.example.expected_document_type!r} "
                f"v{outcome.example.expected_schema_version}, got "
                f"{outcome.actual_document_type!r} v{outcome.actual_schema_version} "
                f"(status={outcome.actual_status})"
            )
        for field_outcome in outcome.field_outcomes:
            if not field_outcome.correct:
                print(
                    f"    field {field_outcome.name!r}: expected {field_outcome.expected!r}, "
                    f"got {field_outcome.actual!r}"
                )

    classification_by_type: dict[str, list[bool]] = defaultdict(list)
    # Keyed by (Document Type, Field name), not Field name alone — two Document Types could
    # each have a same-named Field (e.g. two Types both with `totalAmount`), and those must
    # never conflate into one shared accuracy figure.
    field_by_type_and_name: dict[tuple[str, str], list[bool]] = defaultdict(list)
    for outcome in outcomes:
        doc_type = outcome.example.expected_document_type or "(unclassified)"
        classification_by_type[doc_type].append(outcome.classification_correct)
        for field_outcome in outcome.field_outcomes:
            field_by_type_and_name[(doc_type, field_outcome.name)].append(field_outcome.correct)

    print("\nClassification accuracy by Document Type:")
    for doc_type, results in sorted(classification_by_type.items()):
        _print_accuracy_row(doc_type, results)

    print("\nExtraction accuracy by Document Type / Field:")
    for (doc_type, field_name), results in sorted(field_by_type_and_name.items()):
        _print_accuracy_row(f"{doc_type}.{field_name}", results)

    total = len(outcomes)
    fully_correct = sum(1 for outcome in outcomes if outcome.fully_correct)
    print(f"\nOverall: {fully_correct}/{total} examples fully correct ({_pct(fully_correct, total)})")


async def _amain(golden_dir: Path, model: str | None) -> int:
    settings = get_settings()
    schema_registry = SchemaRegistry.load(settings.schema_registry_dir)
    examples = load_golden_examples(golden_dir)
    if not examples:
        print(f"No golden examples found under {golden_dir}", file=sys.stderr)
        return 1

    client = anthropic.AsyncAnthropic()
    inner_provider = AnthropicModelProvider(client, **({"model": model} if model else {}))
    model_provider = RetryingModelProvider(inner_provider)
    session_factory = async_sessionmaker(make_engine(), expire_on_commit=False)

    outcomes = []
    async with get_s3_client() as s3_client:
        deps = PipelineDeps(
            session_factory=session_factory,
            s3_client=s3_client,
            bucket=settings.s3_bucket,
            model_provider=model_provider,
            schema_registry=schema_registry,
        )
        for example in examples:
            print(f"running {example.name}...", file=sys.stderr)
            job = await _run_example(deps, example)
            outcomes.append(_evaluate(example, job))

    print_report(outcomes)
    return 0 if all(outcome.fully_correct for outcome in outcomes) else 1


def main() -> None:
    # `anthropic.AsyncAnthropic()` (below) reads `ANTHROPIC_API_KEY` straight from the process
    # environment, unlike `Settings` (config.py), which parses `.env` itself via
    # pydantic-settings — so it needs `.env` loaded into the environment explicitly here.
    load_dotenv()

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--golden-dir", type=Path, default=Path(__file__).parent / "golden", help="Golden examples root"
    )
    parser.add_argument("--model", default=None, help="Override the Anthropic model to evaluate")
    args = parser.parse_args()
    raise SystemExit(asyncio.run(_amain(args.golden_dir, args.model)))


if __name__ == "__main__":
    main()
