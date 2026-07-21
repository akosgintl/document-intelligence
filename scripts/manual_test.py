#!/usr/bin/env python3
"""Manually exercise the Document Intelligence API: submit a file, poll until
the Job finishes, and print the result.

Usage:
    uv run python scripts/manual_test.py [file] [--base-url URL] [--api-key KEY]
                                          [--interval SECONDS] [--timeout SECONDS]

With no file argument, submits scripts/samples/invoice.pdf (generate it first
with `uv run python scripts/generate_sample_invoice.py` if it's missing).
"""

import argparse
import json
import mimetypes
import sys
import time
from pathlib import Path

import httpx

DEFAULT_SAMPLE = Path(__file__).parent / "samples" / "invoice.pdf"
SUPPORTED_CONTENT_TYPES = {"application/pdf", "image/png", "image/jpeg", "image/webp"}
TERMINAL_STATUSES = {"complete", "failed"}


def _content_type(path: Path) -> str:
    guess, _ = mimetypes.guess_type(path.name)
    if guess not in SUPPORTED_CONTENT_TYPES:
        raise SystemExit(f"Unsupported file type for {path.name} (need .pdf/.png/.jpg/.webp)")
    return guess


def _fail(response: httpx.Response) -> None:
    print(f"HTTP {response.status_code}: {response.text}", file=sys.stderr)
    raise SystemExit(1)


def submit(client: httpx.Client, path: Path) -> str:
    content_type = _content_type(path)
    response = client.post(
        "/v1/submissions",
        files={"file": (path.name, path.read_bytes(), content_type)},
    )
    if response.status_code != 202:
        _fail(response)
    body = response.json()
    print(f"submitted {path.name} -> job {body['job_id']} ({content_type})")
    return body["job_id"]


def poll(client: httpx.Client, job_id: str, *, interval: float, timeout: float) -> dict:
    deadline = time.monotonic() + timeout
    last_status = None
    body: dict = {}
    while time.monotonic() < deadline:
        response = client.get(f"/v1/jobs/{job_id}")
        if response.status_code != 200:
            _fail(response)
        body = response.json()
        if body["status"] != last_status:
            print(f"  status: {body['status']}")
            last_status = body["status"]
        if body["status"] in TERMINAL_STATUSES:
            return body
        time.sleep(interval)
    print(f"timed out after {timeout}s waiting for job {job_id}", file=sys.stderr)
    return body


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", nargs="?", type=Path, default=DEFAULT_SAMPLE)
    parser.add_argument("--base-url", default="http://localhost:8000")
    parser.add_argument("--api-key", default="dev-local-api-key")
    parser.add_argument("--interval", type=float, default=1.0)
    parser.add_argument("--timeout", type=float, default=60.0)
    args = parser.parse_args()

    if not args.file.exists():
        raise SystemExit(
            f"No such file: {args.file}\n"
            "Generate the sample first: uv run python scripts/generate_sample_invoice.py"
        )

    with httpx.Client(
        base_url=args.base_url,
        headers={"Authorization": f"Bearer {args.api_key}"},
        timeout=30.0,
    ) as client:
        job_id = submit(client, args.file)
        result = poll(client, job_id, interval=args.interval, timeout=args.timeout)

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
