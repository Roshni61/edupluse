import os
from datetime import date
# Ensure test DB is in-memory SQLite before loading app config
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db.session import Base, get_db
from app.core.security import create_access_token, get_password_hash
from app.models.models import (
    School,
    User,
    Class,
    ClassTeacher,
    Student,
    ParentLink,
    Assessment,
    Score,
    Attendance,
    HomeworkRecord,
    SupportSnapshot,
    Mission,
    GardenDrop,
    XpLedger,
    Badge,
)

SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db_session():
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def seed_data(db_session):
    # Schools
    school1 = School(id="sch-1", name="School One")
    school2 = School(id="sch-2", name="School Two")
    db_session.add_all([school1, school2])
    db_session.commit()

    # Classes
    class_9a = Class(id="cls-9a", school_id="sch-1", name="9A", grade="9")
    db_session.add(class_9a)
    db_session.commit()

    # Users in School 1
    teacher = User(
        id="usr-teacher",
        school_id="sch-1",
        name="Ms. Teacher",
        email="teacher@test.com",
        password_hash=get_password_hash("pass"),
        role="teacher",
        language="en",
    )
    student_user = User(
        id="usr-student",
        school_id="sch-1",
        name="Student Test",
        email="student@test.com",
        password_hash=get_password_hash("pass"),
        role="student",
        language="en",
    )
    parent_user = User(
        id="usr-parent",
        school_id="sch-1",
        name="Parent Test",
        email="parent@test.com",
        password_hash=get_password_hash("pass"),
        role="parent",
        language="ta",
    )
    other_parent = User(
        id="usr-parent-2",
        school_id="sch-1",
        name="Other Parent",
        email="other_parent@test.com",
        password_hash=get_password_hash("pass"),
        role="parent",
        language="en",
    )
    admin_user = User(
        id="usr-admin",
        school_id="sch-1",
        name="Admin Test",
        email="admin@test.com",
        password_hash=get_password_hash("pass"),
        role="admin",
        language="en",
    )

    db_session.add_all([teacher, student_user, parent_user, other_parent, admin_user])
    db_session.commit()

    # Class Teacher
    ct = ClassTeacher(
        id="ct-1",
        class_id="cls-9a",
        teacher_id="usr-teacher",
        subject="Maths",
    )
    db_session.add(ct)

    # Student record in School 1
    student = Student(
        id="stu-1",
        user_id="usr-student",
        class_id="cls-9a",
        roll_no="1",
    )
    db_session.add(student)
    db_session.commit()

    # Parent Link
    pl = ParentLink(
        id="pl-1",
        parent_user_id="usr-parent",
        student_id="stu-1",
        relation="Mother",
        preferred_channel="whatsapp",
        preferred_language="ta",
    )
    db_session.add(pl)

    # Support Snapshot
    snap = SupportSnapshot(
        id="ss-1",
        student_id="stu-1",
        level=2,
        reasons=["Drop in math scores"],
        minutes=10,
        benefit=80,
        baseline=75,
        drop=10,
    )
    db_session.add(snap)

    # Assessments & Scores (T1 to T5)
    for i, mark in enumerate([75, 74, 76, 75, 65], start=1):
        ass = Assessment(
            id=f"ass-{i}",
            class_id="cls-9a",
            subject="Maths",
            label=f"T{i}",
            held_on=date(2026, 1, i),
        )
        db_session.add(ass)
        sc = Score(
            id=f"sc-{i}",
            student_id="stu-1",
            assessment_id=f"ass-{i}",
            marks=mark,
        )
        db_session.add(sc)

    # Attendance: 17 present, 3 absent (85%)
    for i in range(1, 21):
        db_session.add(Attendance(
            id=f"att-{i}",
            student_id="stu-1",
            date=date(2026, 1, i),
            present=(i <= 17),
        ))

    # Homework: 8 on_time, 2 late (80%)
    for i in range(1, 11):
        db_session.add(HomeworkRecord(
            id=f"hw-{i}",
            student_id="stu-1",
            subject="Maths",
            due_date=date(2026, 1, i),
            status="on_time" if i <= 8 else "late",
        ))

    # Initial XP (100)
    db_session.add(XpLedger(
        id="xp-init",
        student_id="stu-1",
        delta=100,
        reason="Initial effort",
    ))

    # Mission
    mission = Mission(
        id="m1",
        title="Fraction Practice",
        minutes=5,
        xp=30,
        tier="Starter",
        kind="quiz",
        blurb="Short practice",
    )
    db_session.add(mission)

    # Garden Drops (10 drops for 9A)
    for i in range(10):
        db_session.add(GardenDrop(
            id=f"gd-{i}",
            class_id="cls-9a",
            student_id=None,
        ))

    db_session.commit()
    return {
        "school1": school1,
        "school2": school2,
        "class_9a": class_9a,
        "teacher": teacher,
        "student": student_user,
        "parent": parent_user,
        "other_parent": other_parent,
        "admin": admin_user,
        "student_record": student,
        "mission": mission,
    }


@pytest.fixture
def teacher_token(seed_data):
    return create_access_token(subject=seed_data["teacher"].id, role="teacher", school_id="sch-1")


@pytest.fixture
def student_token(seed_data):
    return create_access_token(subject=seed_data["student"].id, role="student", school_id="sch-1")


@pytest.fixture
def parent_token(seed_data):
    return create_access_token(subject=seed_data["parent"].id, role="parent", school_id="sch-1")


@pytest.fixture
def other_parent_token(seed_data):
    return create_access_token(subject=seed_data["other_parent"].id, role="parent", school_id="sch-1")


@pytest.fixture
def admin_token(seed_data):
    return create_access_token(subject=seed_data["admin"].id, role="admin", school_id="sch-1")
