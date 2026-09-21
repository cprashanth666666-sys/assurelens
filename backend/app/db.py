"""Database engine and session management.

The engine is built lazily rather than at import.

/api/health exists to report that the database is unreachable instead of
failing on it. Constructing the engine at module scope defeated that: an
unparseable DATABASE_URL raised ArgumentError before FastAPI was constructed,
so the app did not boot at all and the operator saw a generic startup failure
with no diagnostic. Deferring construction lets health answer, and say which
kind of problem it is — configuration or connectivity.
"""

from collections.abc import Iterator

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings

# Bounded so /api/health always answers promptly. Long enough for a genuine
# cold start to succeed, short enough that an unreachable host is reported
# rather than waited on.
CONNECT_TIMEOUT_SECONDS = 5


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


class DatabaseConfigurationError(RuntimeError):
    """DATABASE_URL could not be parsed.

    Distinct from a connection failure: this is a deployment mistake that no
    amount of waiting will fix, and health reports it as such.
    """


_engine: Engine | None = None
_session_factory: sessionmaker[Session] | None = None


def get_engine() -> Engine:
    """Build the engine on first use, then reuse it."""
    global _engine
    if _engine is None:
        try:
            _engine = create_engine(
                get_settings().database_url,
                pool_pre_ping=True,  # Render free tier drops idle connections.
                future=True,
                # Health is called on first paint to wake a sleeping backend,
                # so it has to answer quickly. Without a bound, a connect to
                # an unreachable host hangs on the OS default — measured at
                # over two minutes locally — and the page sits on a spinner,
                # which is the exact cold-start experience TRD 1.4 exists to
                # prevent.
                connect_args={"connect_timeout": CONNECT_TIMEOUT_SECONDS},
            )
        except Exception as exc:
            raise DatabaseConfigurationError(str(exc)) from exc
    return _engine


def get_session_factory() -> sessionmaker[Session]:
    global _session_factory
    if _session_factory is None:
        _session_factory = sessionmaker(
            bind=get_engine(), autoflush=False, expire_on_commit=False
        )
    return _session_factory


def get_db() -> Iterator[Session]:
    """FastAPI dependency yielding a request-scoped session."""
    db = get_session_factory()()
    try:
        yield db
    finally:
        db.close()
