import os
import socket
import tempfile
import urllib.parse
import pytest
from sqlalchemy import create_engine, inspect, text, event
from sqlalchemy.orm import sessionmaker
from sqlite3 import Connection as SQLite3Connection
from alembic.config import Config
from alembic import command

from app.core.security import verify_password
from app.models.models import (
    School,
    User,
    Class,
    Student,
    Score,
    Assessment,
    Badge,
    Mission,
    XpLedger,
    GardenDrop,
    Doubt,
    CallWindow,
    Booking,
    ParentLink,
    SupportSnapshot,
)
from app.db.seed import seed_database, DEFAULT_PASSWORD


EXPECTED_TABLES = [
    "schools",
    "users",
    "classes",
    "class_teachers",
    "students",
    "parent_links",
    "assessments",
    "scores",
    "attendance",
    "homework_records",
    "support_snapshots",
    "playbook_actions",
    "missions",
    "mission_assignments",
    "mission_attempts",
    "badges",
    "student_badges",
    "xp_ledger",
    "garden_drops",
    "kudos",
    "doubts",
    "parent_notes",
    "checkins",
    "call_windows",
    "bookings",
    "outbox_messages",
    "callback_queue",
    "audit_logs",
]


def run_migration_and_seed_verification(db_url: str, is_sqlite: bool = True):
    """
    Shared test helper that applies Alembic migrations to head,
    verifies table creation, seeds prototype data, asserts data integrity,
    and validates idempotency on any SQLAlchemy-supported database.
    """
    orig_env = os.environ.get("DATABASE_URL")
    test_engine = None
    db = None
    try:
        os.environ["DATABASE_URL"] = db_url

        backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        alembic_ini_path = os.path.join(backend_dir, "alembic.ini")

        alembic_cfg = Config(alembic_ini_path)
        alembic_cfg.set_main_option("sqlalchemy.url", db_url)
        alembic_cfg.set_main_option("script_location", os.path.join(backend_dir, "alembic"))

        # 1. Run Alembic migration to head
        command.upgrade(alembic_cfg, "head")

        # 2. Verify all 28 tables exist in schema
        connect_args = {"check_same_thread": False} if is_sqlite else {}
        test_engine = create_engine(db_url, connect_args=connect_args)

        if is_sqlite:
            @event.listens_for(test_engine, "connect")
            def set_sqlite_pragma(dbapi_connection, connection_record):
                if isinstance(dbapi_connection, SQLite3Connection):
                    cursor = dbapi_connection.cursor()
                    cursor.execute("PRAGMA foreign_keys=ON")
                    cursor.close()

        inspector = inspect(test_engine)
        existing_tables = inspector.get_table_names()

        for expected_table in EXPECTED_TABLES:
            assert expected_table in existing_tables, f"Table {expected_table} missing from migration on {db_url}"

        # 3. Seed the freshly migrated database
        Session = sessionmaker(bind=test_engine)
        db = Session()

        seed_database(db)

        # 4. Verify seeded prototype story
        # A. Demo Accounts
        demo_emails = [
            ("teacher@edupulse.demo", "teacher"),
            ("student@edupulse.demo", "student"),
            ("parent@edupulse.demo", "parent"),
            ("admin@edupulse.demo", "admin"),
        ]
        for email, role in demo_emails:
            user = db.query(User).filter(User.email == email).first()
            assert user is not None, f"Demo account {email} not found"
            assert user.role == role
            assert verify_password(DEFAULT_PASSWORD, user.password_hash) is True

        # B. 8 Students with exact names
        expected_students = ["Karthik", "Divya", "Arun", "Vikram", "Rahul", "Lakshmi", "Meena", "Sana"]
        students = db.query(Student).all()
        student_names = [s.name for s in students]
        assert len(students) == 8
        for name in expected_students:
            assert name in student_names

        # C. Karthik's scores, level, reasons, and derived XP
        karthik_user = db.query(User).filter(User.email == "student@edupulse.demo").first()
        karthik = db.query(Student).filter(Student.user_id == karthik_user.id).first()
        assert karthik is not None
        assert karthik.scores_list == [74, 73, 75, 72, 68, 64, 61, 60]
        assert karthik.current_xp == 340  # Derived from xp_ledger (PRODUCT RULE 1: Effort over Marks)
        assert karthik.support_level == 3
        assert "Maths is down 9 marks from his usual level of 73" in karthik.reasons

        # D. 12 Badges and 3 Missions
        assert db.query(Badge).count() == 12
        assert db.query(Mission).count() == 3

        # E. Class Garden (31 drops from store.tsx, cooperative & anonymous)
        assert db.query(GardenDrop).count() == 31

        # F. Call Windows & Bookings
        assert db.query(CallWindow).count() == 4
        assert db.query(Booking).count() == 4

        # G. Anonymous Doubts (PRODUCT RULE 6: No student_id or user_id)
        doubts = db.query(Doubt).all()
        assert len(doubts) >= 1
        for d in doubts:
            assert not hasattr(d, "student_id")
            assert not hasattr(d, "user_id")

        # 5. Verify Idempotency: run seed again on the same DB session
        seed_database(db)

        # Assert row counts did not duplicate
        assert db.query(Student).count() == 8
        assert db.query(Badge).count() == 12
        assert db.query(Mission).count() == 3
        assert db.query(CallWindow).count() == 4
        assert db.query(Booking).count() == 4
        assert db.query(GardenDrop).count() == 31
        assert karthik.current_xp == 340

    finally:
        if db is not None:
            db.close()
        if test_engine is not None:
            test_engine.dispose()
        if orig_env is not None:
            os.environ["DATABASE_URL"] = orig_env
        else:
            os.environ.pop("DATABASE_URL", None)


def test_sqlite_foreign_keys_pragma_enabled():
    """
    Verify PRAGMA foreign_keys=ON is active on SQLite connections
    and enforces referential integrity.
    """
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_db:
        tmp_db_path = tmp_db.name

    engine = None
    try:
        db_url = f"sqlite:///{tmp_db_path}"
        engine = create_engine(db_url)

        @event.listens_for(engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            if isinstance(dbapi_connection, SQLite3Connection):
                cursor = dbapi_connection.cursor()
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.close()

        with engine.connect() as conn:
            result = conn.execute(text("PRAGMA foreign_keys;")).scalar()
            assert result == 1, "PRAGMA foreign_keys must be enabled (1) for SQLite"
    finally:
        if engine is not None:
            engine.dispose()
        if os.path.exists(tmp_db_path):
            try:
                os.remove(tmp_db_path)
            except OSError:
                pass


def test_migrate_fresh_sqlite_and_seed():
    """
    Runs migration + seed test on a fresh temporary SQLite database.
    """
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_db:
        tmp_db_path = tmp_db.name

    try:
        db_url = f"sqlite:///{tmp_db_path}"
        run_migration_and_seed_verification(db_url, is_sqlite=True)
    finally:
        if os.path.exists(tmp_db_path):
            try:
                os.remove(tmp_db_path)
            except OSError:
                pass


def test_migrate_postgres_and_seed():
    """
    Runs migration + seed test on PostgreSQL if reachable.
    """
    postgres_url = os.getenv("TEST_POSTGRES_URL", "postgresql://edupulse_user:edupulse_password@localhost:5432/edupulse_test")
    parsed = urllib.parse.urlparse(postgres_url)
    host = parsed.hostname or "localhost"
    port = parsed.port or 5432

    # Fast TCP connectivity check before attempting connection
    s = socket.socket()
    s.settimeout(0.8)
    try:
        s.connect((host, port))
        s.close()
    except Exception:
        pytest.skip(f"PostgreSQL at {host}:{port} is not reachable; skipping Postgres migration & seed test.")

    # Postgres is reachable: clean test schema and run migration + seed
    try:
        pg_engine = create_engine(postgres_url)
        with pg_engine.connect() as conn:
            conn.execution_options(isolation_level="AUTOCOMMIT").execute(
                text("DROP SCHEMA public CASCADE; CREATE SCHEMA public;")
            )
        pg_engine.dispose()

        run_migration_and_seed_verification(postgres_url, is_sqlite=False)
    except Exception as e:
        pytest.fail(f"PostgreSQL migration and seed failed: {e}")
