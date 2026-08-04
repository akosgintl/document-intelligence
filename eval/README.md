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
    "schema_version": 2,
    "fields": {
      "invoiceNumber": "2026/B/00417",
      "grossTotal": 5086616
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
`eval/golden/invoice/happy_path/`, grouped by Document Type) is just for organization — the
directory name has no effect on evaluation.

## What is committed

Two examples per Document Type — one happy path, one whose nulls target that type's most
contestable Schema decision (#46, convention 3).

| Example | What it is | What it is here to catch |
| --- | --- | --- |
| `invoice/happy_path` | A NAV-complete Hungarian invoice, settled by transfer | Its `vatSummary` and its totals block **disagree by 1 Ft**, which is legitimate rounding and must survive extraction rather than being reconciled; `vatRate` prints `27%`, `fordított adózás` and `TAM` in one column |
| `invoice/simplified` | An *egyszerűsített számla* — a gross-only counter sale | The page says so, but **no Field records it**: null `netAmount` on every line, null `netTotal`/`vatTotal`, and `vatSummary` null as a whole array, is all an extracted Document has to read it by |

The eight examples for the four Hungarian identity types are still to be authored (#53, #54,
#55, #58).

### Measured baseline

`claude-sonnet-5` (the `AnthropicModelProvider` default), 2026-08-04, **6 replicated runs**:
12/12 example-evaluations fully correct — classification 12/12 at `classified`, and every one
of the 18 Fields correct on every run, `lineItems` and `vatSummary` included. Those two compare
by exact `==` over the whole nested value (`_values_match` applies its ±0.01 tolerance only at
the top level), so a single wrong row or a missing null would have shown.

The figure worth naming: **the 1 Ft rounding disagreement survived extraction intact in all six
runs.** The model transcribed `vatSummary`'s 47 115 and the totals block's 47 116 as printed
rather than reconciling them — which is what #43 kept both blocks for.

Replicate before reading anything into a change here. #49 measured this Provider as returning a
*draw*, not a reading — `anthropic_provider.py` sets no `temperature` — so a single run that
differs is not yet a regression.

The two `invoice/*` examples that predated the renderer were **unrecoverably broken** — they
pinned `schema_version: 1`, classification binds to the latest version, and invoice v2 has
neither `vendorName` nor `totalAmount` — so they and their generator were deleted rather than
patched (#46, convention 4; #51 and #56).
