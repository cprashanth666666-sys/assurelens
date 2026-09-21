"""Settings must fail loudly on missing config and repair a scheme-less host."""

import pytest
from pydantic import ValidationError

from app.config import Settings


def test_database_url_is_required(monkeypatch: pytest.MonkeyPatch) -> None:
    """No default. A missing DATABASE_URL is a deployment mistake, not an outage.

    With a localhost default, an unbound environment variable let the app
    start successfully and report `database: down` — indistinguishable from a
    sleeping database, so nobody looked at the configuration.
    """
    monkeypatch.delenv("DATABASE_URL", raising=False)

    with pytest.raises(ValidationError):
        Settings(_env_file=None)  # type: ignore[call-arg]


@pytest.mark.parametrize(
    ("given", "expected"),
    [
        # Render's fromService injection yields a scheme-less host. Passed to
        # httpx unchanged it raises UnsupportedProtocol, and every probe
        # control then gates on G8_TARGET_UNREACHABLE — a configuration error
        # wearing the costume of a correct assurance verdict.
        ("assurelens-target.onrender.com", "https://assurelens-target.onrender.com"),
        ("assurelens-target.onrender.com:443", "https://assurelens-target.onrender.com:443"),
        ("localhost:8001", "http://localhost:8001"),
        ("127.0.0.1:8001", "http://127.0.0.1:8001"),
        ("target_service:8001", "http://target_service:8001"),
        # Already-valid URLs pass through, trailing slash normalised.
        ("http://localhost:8001", "http://localhost:8001"),
        ("https://example.test/", "https://example.test"),
    ],
)
def test_target_service_url_gets_a_scheme(
    given: str, expected: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://u:p@localhost:5432/d")

    settings = Settings(_env_file=None, target_service_url=given)  # type: ignore[call-arg]

    assert settings.target_service_url == expected


def test_empty_target_service_url_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://u:p@localhost:5432/d")

    with pytest.raises(ValidationError):
        Settings(_env_file=None, target_service_url="   ")  # type: ignore[call-arg]


def test_cors_origins_never_defaults_to_wildcard(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://u:p@localhost:5432/d")

    settings = Settings(_env_file=None)  # type: ignore[call-arg]

    assert "*" not in settings.cors_origins


@pytest.mark.parametrize(
    ("given", "expected"),
    [
        # What Neon, Supabase and Render actually hand you.
        (
            "postgresql://u:p@ep-cool-name-123.ap-southeast-1.aws.neon.tech/assurelens?sslmode=require",
            "postgresql+psycopg://u:p@ep-cool-name-123.ap-southeast-1.aws.neon.tech/assurelens?sslmode=require",
        ),
        # Heroku-style legacy prefix.
        ("postgres://u:p@h:5432/d", "postgresql+psycopg://u:p@h:5432/d"),
        # Already correct — left alone.
        ("postgresql+psycopg://u:p@h:5432/d", "postgresql+psycopg://u:p@h:5432/d"),
    ],
)
def test_database_url_driver_is_normalised(given: str, expected: str) -> None:
    """Pasting a host's connection string verbatim must not fail at startup.

    Without the driver named, SQLAlchemy reaches for psycopg2, which is not
    installed, and the app dies with a ModuleNotFoundError that says nothing
    about the real cause.
    """
    settings = Settings(_env_file=None, database_url=given)  # type: ignore[call-arg]

    assert settings.database_url == expected


def test_sslmode_is_preserved() -> None:
    """Neon requires TLS; dropping the query string would break the connection."""
    settings = Settings(  # type: ignore[call-arg]
        _env_file=None,
        database_url="postgresql://u:p@ep-x.aws.neon.tech/db?sslmode=require&channel_binding=require",
    )

    assert "sslmode=require" in settings.database_url
    assert "channel_binding=require" in settings.database_url
