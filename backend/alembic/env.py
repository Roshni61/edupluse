import os
import sys
from logging.config import fileConfig
from sqlite3 import Connection as SQLite3Connection
from sqlalchemy import engine_from_config, pool, event, text as sa_text
from alembic import context

# Add backend directory to sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.core.config import settings
from app.models.models import Base

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

# Read DATABASE_URL from the environment (same settings object the app uses),
# falling back to alembic.ini only if unset.
db_url = os.getenv("DATABASE_URL") or getattr(settings, "DATABASE_URL", None)
if db_url:
    config.set_main_option("sqlalchemy.url", db_url)


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url") or ""
    is_sqlite = url.startswith("sqlite")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=is_sqlite,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    configuration = config.get_section(config.config_ini_section, {})
    url = config.get_main_option("sqlalchemy.url") or ""
    configuration["sqlalchemy.url"] = url

    is_sqlite = url.startswith("sqlite")
    connect_args = {}
    if is_sqlite:
        connect_args = {"check_same_thread": False}

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        connect_args=connect_args,
    )

    # Enable PRAGMA foreign_keys=ON for SQLite connections
    if is_sqlite:
        @event.listens_for(connectable, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            if isinstance(dbapi_connection, SQLite3Connection):
                cursor = dbapi_connection.cursor()
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.close()

    with connectable.connect() as connection:
        if is_sqlite:
            connection.execute(sa_text("PRAGMA foreign_keys=ON"))

        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=is_sqlite,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
