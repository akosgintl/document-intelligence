# document-intelligence

A schema-based document classification and extraction system. See `CONTEXT.md` for domain vocabulary and `docs/adr/` for architectural decisions.

## Stack

FastAPI, PostgreSQL, Redis + `arq` worker, and MinIO (S3-compatible object storage) — see [ADR-0006](docs/adr/0006-technology-stack.md).

## Running the stack locally

Bring up the API, Postgres, Redis, the `arq` worker, and MinIO together:

```sh
docker compose up -d
```

A one-off `migrate` service applies pending Alembic migrations before the API and worker start; the API then serves on `http://localhost:8000`. Check that everything's connected:

```sh
curl http://localhost:8000/health
```

```json
{"status":"ok","checks":{"postgres":{"ok":true,"error":null},"redis":{"ok":true,"error":null},"storage":{"ok":true,"error":null}}}
```

`status` is `degraded` (HTTP 503) if any dependency is unreachable, with the specific error under that check's `error` key.

Tear the stack down:

```sh
docker compose down       # stop containers, keep data volumes
docker compose down -v    # stop containers and delete data volumes
```

## Local development (without Docker for the app itself)

Requires [`uv`](https://docs.astral.sh/uv/).

```sh
uv sync                                          # install dependencies
docker compose up -d postgres redis minio minio-createbucket
cp .env.example .env                             # point at the docker-composed dependencies
uv run alembic upgrade head
uv run uvicorn document_intelligence.main:app --reload
uv run arq document_intelligence.worker.WorkerSettings   # in a separate terminal
```

## Manual testing

### Connecting to Postgres (e.g. pgAdmin)

Postgres is published to the host on its default port, so point pgAdmin (or any client) at:

- Host: `localhost` (from Windows with WSL2, `localhost` reaches the WSL2 container's published port by default; if it doesn't resolve, use the WSL IP from `hostname -I` run inside WSL instead)
- Port: `5432`
- Database: `document_intelligence`
- User / password: `postgres` / `postgres`

### Browsing MinIO

MinIO's web console is published alongside its S3 API:

- Console: http://localhost:9001
- Login: `minioadmin` / `minioadmin`
- Bucket: `document-intelligence` (created automatically by the `minio-createbucket` service)

(Port `9000` is the S3 API the app itself talks to — not for browser use.)

### Anthropic API key

The `worker`'s real `AnthropicModelProvider` needs a real key. Add it to your local `.env` before starting the stack:

```
ANTHROPIC_API_KEY=sk-ant-...
```

`docker compose up` reads this from `.env` for the `worker` service; `uv run arq document_intelligence.worker.WorkerSettings` picks it up the same way when running outside Docker (`uv run` auto-loads `.env`). Without it, `docker compose up` will fail fast on the `worker` service with a missing-variable error rather than starting a worker that can't classify or extract anything.

### Submitting a document

With the stack up (`docker compose up -d`) and `ANTHROPIC_API_KEY` set, submit the committed sample invoice and poll until it finishes:

```sh
uv run python scripts/manual_test.py
```

This posts `scripts/samples/invoice.pdf` to `POST /v1/submissions`, polls `GET /v1/jobs/{job_id}` until the Job completes, and prints the extracted fields. Pass a different file to test your own PDF/PNG/JPEG/WebP:

```sh
uv run python scripts/manual_test.py path/to/your/document.pdf
```

Regenerate the sample invoice (e.g. to change its fields) with:

```sh
uv run python scripts/generate_sample_invoice.py
```

Equivalent plain `curl`, if you'd rather not run the script:

```sh
curl -s -X POST http://localhost:8000/v1/submissions \
  -H "Authorization: Bearer dev-local-api-key" \
  -F "file=@scripts/samples/invoice.pdf;type=application/pdf"
# -> {"job_id": "...", "status": "pending"}

curl -s http://localhost:8000/v1/jobs/<job_id> \
  -H "Authorization: Bearer dev-local-api-key"
```

## Schema Registry

`SchemaRegistry.load(directory)` (`src/document_intelligence/schema_registry/`) loads every registered Document Type from a directory at startup, one subdirectory per Document Type:

```
<directory>/
  invoice/
    config.json   # {"confidence_threshold": 0.8}
    v1.json       # JSON Schema document
    v2.json
  passport/
    config.json
    v1.json
```

Schema version is a plain incrementing integer taken from each `vN.json` filename ([ADR-0007](docs/adr/0007-schema-version-integer.md)) — never a field inside the Schema content itself. Confidence Threshold is required per Document Type with no system-wide default ([ADR-0004](docs/adr/0004-confidence-threshold-separate-from-schema.md)): loading fails loudly if any Document Type's `config.json` is missing or doesn't set one.

**Operator invariant, not code-enforced:** a Schema version is immutable once any Document has been processed against it. The Registry doesn't check this — doing so needs the database's record of what's been processed, which doesn't exist until the Job/Document persistence layer is built. Until then, treating a `vN.json` file as append-only once it's live is on whoever maintains the registry directory.

## Tests

```sh
uv run pytest
```

## Migrations

Schema migrations are managed with [Alembic](https://alembic.sqlalchemy.org/), rooted at `migrations/`.

```sh
uv run alembic revision -m "description"   # create a new migration
uv run alembic upgrade head                # apply
uv run alembic downgrade -1                # roll back one revision
```
