"""Application settings, loaded from the environment only.

Secrets never appear in code, and no default is supplied that would silently
"work" in production. A missing DATABASE_URL must fail loudly at startup, not
present itself as a database that happens to be down.
"""

from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Required, deliberately. A default pointing at localhost would let a
    # missing or unbound environment variable start the app successfully and
    # report `database: down` — indistinguishable from a sleeping database,
    # so the operator waits for a cold start that never finishes. The local
    # value lives in .env.example, where it cannot reach production.
    database_url: str

    # Comma-separated. Locked to the frontend origin — never "*". [TRD 9]
    cors_allow_origins: str = "http://localhost:3000"

    # Suite 3 reaches the deliberately-vulnerable target over HTTP only. [TRD 1.2]
    target_service_url: str = "http://localhost:8001"

    # Where the control library YAML lives. Empty means "derive from the
    # source tree", which is right for a venv checkout. It is set explicitly
    # in the container, because deriving it there produced "/controls" — a
    # path that only existed because docker-compose happened to bind-mount it
    # at exactly that spot, and which does not exist on a real deployment.
    controls_dir: str = ""

    # Every run records the seed it used, so results are reproducible. [TRD 3.4]
    default_seed: int = 42

    log_level: str = "INFO"
    engine_version: str = "0.1.0"

    # --- Document intake ----------------------------------------------------
    # Raw bytes never go into Postgres — see migration 0006's docstring.
    #
    # "local" is correct for docker-compose and for a host with a real
    # persistent disk. It is WRONG on Render's free plan, which this project
    # actually deploys on (render.yaml): free-plan services have no
    # persistent-disk option, so the container filesystem — and every
    # uploaded document in it — is wiped on the next deploy or scale-to-zero
    # cycle. "s3" (Cloudflare R2's free tier, or any S3-compatible bucket) is
    # what production must set, the same reasoning that put Postgres on Neon
    # rather than Render's own free database. See ingest/storage.py.
    storage_backend: str = "local"
    document_storage_dir: str = "/tmp/assurelens-documents"

    s3_bucket: str = ""
    # Empty means "real AWS S3"; set to R2's account endpoint
    # (https://<account-id>.r2.cloudflarestorage.com) for Cloudflare.
    s3_endpoint_url: str = ""
    s3_region: str = "auto"
    s3_access_key_id: str = ""
    s3_secret_access_key: str = ""

    # 25MB: generous for a policy PDF, small enough that a handful of
    # concurrent uploads cannot exhaust a free-tier container's disk.
    document_max_size_bytes: int = 25 * 1024 * 1024
    # Extracted text kept inline in the database, matching the evidence
    # payload pattern (small, queryable). Beyond this it is truncated and the
    # full text goes to storage instead. [SCHEMA D4 precedent]
    document_max_inline_text_chars: int = 200_000

    @field_validator("storage_backend")
    @classmethod
    def _validate_storage_backend(cls, value: str) -> str:
        value = value.strip().lower()
        if value not in ("local", "s3"):
            raise ValueError(f"STORAGE_BACKEND must be 'local' or 's3', got {value!r}")
        return value

    @field_validator("database_url")
    @classmethod
    def _normalise_driver(cls, value: str) -> str:
        """Accept the bare URL every managed host hands out.

        Neon, Supabase and Render all give a "postgresql://" connection
        string, but SQLAlchemy needs the driver named or it reaches for
        psycopg2, which is not installed. Pasting the string verbatim would
        fail at startup with an obscure ModuleNotFoundError — a paste-time
        trap, so it is repaired here rather than documented as a gotcha.
        """
        value = value.strip()
        for bare, driven in (
            ("postgresql://", "postgresql+psycopg://"),
            ("postgres://", "postgresql+psycopg://"),
        ):
            if value.startswith(bare):
                return driven + value[len(bare):]
        return value

    @field_validator("target_service_url")
    @classmethod
    def _ensure_scheme(cls, value: str) -> str:
        """Normalise a scheme-less host into a URL.

        Render's `fromService` env-var injection yields `host:port` with no
        scheme. Passed to httpx unchanged, that raises UnsupportedProtocol —
        and every probe control would then gate on G8_TARGET_UNREACHABLE,
        which looks exactly like correct, designed behaviour. A configuration
        error masquerading as an assurance verdict is the one failure mode
        this product must not have, so the scheme is repaired here rather
        than trusted to the deployment.
        """
        value = value.strip().rstrip("/")
        if not value:
            raise ValueError("target_service_url must not be empty")
        if "://" not in value:
            # Bare localhost is plain HTTP; anything else is assumed public.
            local = value.startswith(("localhost", "127.0.0.1", "target_service"))
            value = f"{'http' if local else 'https'}://{value}"
        return value

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.cors_allow_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]  # values come from the environment
