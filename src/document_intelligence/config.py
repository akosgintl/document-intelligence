from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/document_intelligence"
    redis_url: str = "redis://localhost:6379/0"

    s3_endpoint_url: str = "http://localhost:9000"
    s3_access_key: str = "minioadmin"
    s3_secret_key: str = "minioadmin"
    s3_bucket: str = "document-intelligence"
    s3_region: str = "us-east-1"

    schema_registry_dir: str = "schemas"

    # Single-tenant, config-driven secret (no DB storage, manual rotation via redeploy).
    api_key: str = "dev-local-api-key"

    # Operator-configured, caller-unadjustable Submission limits (#25): a Submission over
    # either is rejected synchronously at POST time, before a Job is ever created.
    max_submission_size_bytes: int = 50 * 1024 * 1024
    max_submission_pages: int = 200

    # How long a Job can sit in `processing` at its final permitted attempt with no further
    # activity before the reconciliation sweep considers it abandoned (#32) — long enough that
    # an attempt still genuinely in flight is never mistaken for one a hard crash orphaned.
    job_stale_after_seconds: int = 300


@lru_cache
def get_settings() -> Settings:
    return Settings()
