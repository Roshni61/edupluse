import logging
import os
from sqlite3 import Connection as SQLite3Connection
from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker
from app.core.config import settings

logger = logging.getLogger(__name__)

db_url = os.getenv("DATABASE_URL", settings.DATABASE_URL)
connect_args = {}
is_sqlite = db_url.startswith("sqlite")

if is_sqlite:
    connect_args = {"check_same_thread": False}

engine = create_engine(db_url, connect_args=connect_args)

# Enable PRAGMA foreign_keys=ON for SQLite connections
if is_sqlite:
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        if isinstance(dbapi_connection, SQLite3Connection):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
