"""Alembic environment. Reads the database URL from application settings."""

from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from sqlalchemy.exc import OperationalError

from alembic import context
from app.config import get_settings
from app.db import CONNECT_TIMEOUT_SECONDS, Base

config = context.config
config.set_main_option("sqlalchemy.url", get_settings().database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        # Bounded, like the application engine. Without it a wrong or
        # unreachable DATABASE_URL makes this hang indefinitely -- and since
        # migrations run before the server starts, the deploy never fails and
        # never serves. The platform routes traffic to a container that
        # accepts the connection and answers nothing, which looks like a
        # hung application rather than a bad connection string.
        connect_args={"connect_timeout": CONNECT_TIMEOUT_SECONDS},
    )

    try:
        connection_context = connectable.connect()
    except OperationalError as exc:
        raise SystemExit(
            "MIGRATION ABORTED: could not reach the database within "
            f"{CONNECT_TIMEOUT_SECONDS}s. Check DATABASE_URL. "
            "Failing here is deliberate - a migration step that waits forever "
            "produces a service that never starts and never reports why. "
            f"({exc.__class__.__name__}: {exc})"
        ) from exc

    with connection_context as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
