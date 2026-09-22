"""Shared fixtures.

Tests that need the control library run against a real PostgreSQL, because
the schema depends on PostgreSQL-specific types — JSONB, native enums and a
partial unique index. Verifying them against SQLite would prove nothing about
what actually ships.
"""

from __future__ import annotations

import os
from collections.abc import Iterator

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.seed.controls import load_control_library, load_engagement_scope
from app.seed.meridian import load_estate

# Default matches docker-compose, which publishes on host port 5433 to avoid
# a locally installed PostgreSQL service that usually owns 5432.
TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+psycopg://assurelens:change-me-locally@localhost:5433/assurelens",
)


@pytest.fixture(scope="session")
def db_available() -> bool:
    try:
        engine = create_engine(TEST_DATABASE_URL, connect_args={"connect_timeout": 3})
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:  # noqa: BLE001 — absence of a database is a skip, not an error.
        return False


@pytest.fixture(scope="session")
def seeded_db(db_available: bool) -> Iterator[Session]:
    """A session against a database seeded with the real control library.

    Skips rather than fails when no database is reachable, so the fast unit
    suite still runs on a machine without Docker.
    """
    if not db_available:
        pytest.skip(f"No database at {TEST_DATABASE_URL}; run `docker compose up -d postgres`")

    engine = create_engine(TEST_DATABASE_URL)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    with factory() as db:
        _clear_run_history(db)
        load_control_library(db)
        load_engagement_scope(db)
        db.commit()
        yield db


def _clear_run_history(db: Session) -> None:
    """Start every session from a known state.

    The run API commits, because that is what the real code path does. Those
    rows then survive the pytest process and, on the next invocation, pin the
    procedure rows the control-library loader is about to update -- so the
    suite passes once and fails ever after, for reasons that have nothing to
    do with the code under test.

    Truncating here rather than asking tests not to commit: a test that
    avoids the real commit is not testing the real path.
    """
    db.execute(
        text(
            "TRUNCATE test_results, evidence_items, test_runs, audit_log "
            "RESTART IDENTITY CASCADE"
        )
    )
    db.commit()


@pytest.fixture(scope="session")
def seeded_estate(seeded_db: Session) -> Session:
    """The control library plus Meridian's generated estate.

    Seeded once per session: 24,000 principals is a few seconds to build and
    there is no reason to pay it per test. Every test here reads, none write.
    """
    load_estate(seeded_db, seed=42)
    seeded_db.commit()
    return seeded_db
