# Evaluation harness

A golden-dataset accuracy report for the real pipeline — distinct from, and in addition to,
`tests/` (#29). `tests/` uses `FakeModelProvider` for deterministic pass/fail assertions; this
harness runs golden Submissions through the real `AnthropicModelProvider` and reports accuracy,
since a probabilistic Provider makes per-example pytest assertions flaky.

## Running it

Requires Postgres, Redis, and MinIO reachable per `.env` (`docker compose up -d postgres redis
minio minio-createbucket`), migrations applied (`uv run alembic upgrade head`), and a real
`ANTHROPIC_API_KEY` in `.env` — this makes real, billed Model Provider calls.

```sh
uv run python eval/run_eval.py
```

Prints a per-example pass/fail with the specific mismatch when one occurs, then a summary
broken down by Document Type (classification accuracy) and by Field (extraction accuracy).
Exits non-zero if any example didn't fully match its expectation.

Pass `--model` to evaluate a different Anthropic model, or `--golden-dir` to point at a
different golden set.

## Adding a golden example

Golden examples are **not written by hand** — they are drawn by the shared fixture renderer, so
that an example's image and its `expected.json` cannot drift apart. Add a data table to
`fixtures/catalogue.py` (its docstring is the step-by-step) and run:

```sh
uv run python -m fixtures.generate
```

That one command writes both fixture surfaces: the golden examples here, and the manual-testing
samples under `scripts/samples/`. What it produces is the layout below.

### The layout it produces

Each golden example is a directory under `eval/golden/` containing:

- `submission.<ext>` — the file to submit (`.pdf`, `.png`, `.jpg`, or `.webp`)
- `expected.json` — the known-correct result:

  ```json
  {
    "document_type": "invoice",
    "schema_version": 1,
    "fields": {
      "invoiceNumber": "INV-2026-0417",
      "totalAmount": 375.0
    }
  }
  ```

  `schema_version` pins the example to an explicit Schema version (`schemas/<type>/vN.json`) so
  a later version bump can't silently invalidate it. Set `document_type` to `null` (and omit
  `fields`) for an example that's expected to come back `unclassified`. Only Fields you list in
  `fields` are checked — omit a Field the Model Provider is known to be unreliable on rather
  than asserting a value you don't actually expect.

  Numeric Field values are compared with a small tolerance (±0.01); everything else must match
  exactly.

The harness discovers examples by recursively globbing for `expected.json`, so nesting (e.g.
`eval/golden/invoice/basic/`, grouped by Document Type) is just for organization — the directory
name has no effect on evaluation.

The two committed `invoice/*` examples predate the renderer and are **known broken**: they pin
`schema_version: 1`, but classification binds to the latest version and invoice v2 has neither
`vendorName` nor `totalAmount`. They are retired and replaced with v2 examples by
[#56](https://github.com/akosgintl/document-intelligence/issues/56); until then, expect them to
fail a run. Their generator has been absorbed into `fixtures/`.
