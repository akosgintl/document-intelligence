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
