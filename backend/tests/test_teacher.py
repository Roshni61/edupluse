import pytest
from datetime import date, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.db.session import get_db
from app.db.seed import seed_database
from app.core.rate_limiter import login_rate_limiter
from app.core.security import create_access_token, get_password_hash
from app.models.models import (
    School,
    User,
    Student,
    Class,
    ClassTeacher,
    PlaybookAction,
    ParentNote,
    OutboxMessage,
    Kudos,
    AuditLog,
    SupportSnapshot,
)
from app.services.support import (
    change_from_self,
    generate_reasons,
    what_if as calculate_what_if,
    plan_for_time_budget,
    recompute_student_support,
    run_nightly_support_job,
)


@pytest.fixture(autouse=True)
def setup_teacher_test_env(db_session: Session):
    login_rate_limiter.reset()
    seed_database(db_session)
    yield
    login_rate_limiter.reset()


def get_teacher_token(db_session: Session) -> str:
    teacher = db_session.query(User).filter(User.email == "teacher@edupulse.demo").first()
    return create_access_token(subject=teacher.id, role="teacher", school_id=teacher.school_id)


def get_student_token(db_session: Session) -> str:
    student = db_session.query(User).filter(User.email == "student@edupulse.demo").first()
    return create_access_token(subject=student.id, role="student", school_id=student.school_id)


def get_parent_token(db_session: Session) -> str:
    parent = db_session.query(User).filter(User.email == "parent@edupulse.demo").first()
    return create_access_token(subject=parent.id, role="parent", school_id=parent.school_id)


# =========================================================================
# 1. SUPPORT ENGINE UNIT TESTS
# =========================================================================

def test_support_engine_karthik_level_3(db_session: Session):
    """
    Karthik must come out level 3 with exact change-from-self drop and reasons.
    """
    user = db_session.query(User).filter(User.email == "student@edupulse.demo").first()
    assert user is not None
    karthik = db_session.query(Student).filter(Student.user_id == user.id).first()
    assert karthik is not None

    change = change_from_self(karthik)
    assert change["level"] == 3
    assert change["baseline"] == 73
    assert change["drop"] == 9
    assert change["attendance_pct"] == 76
    assert change["homework_pct"] == 60

    reasons = generate_reasons(karthik, change)
    assert any("Maths is down 9 marks from his usual level of 73" in r for r in reasons)
    assert any("Monday absences" in r for r in reasons)
    assert any("Homework late" in r for r in reasons)

    assert karthik.minutes == 8
    assert karthik.benefit == 95


def test_support_engine_meena_level_1_bright(db_session: Session):
    """
    Meena must come out level 1 and marked as a bright spot.
    """
    user = db_session.query(User).filter(User.name == "Meena").first()
    assert user is not None
    meena = db_session.query(Student).filter(Student.user_id == user.id).first()
    assert meena is not None

    change = change_from_self(meena)
    assert change["level"] == 1
    assert meena.bright is True
    assert meena.bright_why == "Up 19 marks over eight tests"
    assert meena.minutes == 0
    assert meena.benefit == 0

    reasons = generate_reasons(meena, change)
    assert len(reasons) == 0  # Bright spots don't have deficiency reasons


def test_stateless_what_if_calculation(db_session: Session):
    """
    Tests stateless 'What If?' slider computation.
    """
    user = db_session.query(User).filter(User.email == "student@edupulse.demo").first()
    karthik = db_session.query(Student).filter(Student.user_id == user.id).first()

    # With full attendance & homework, Karthik's level reduces to 1
    result = calculate_what_if(karthik, attendance=100, homework=100)
    assert result["level"] == 1
    assert result["score"] < 20

    # With moderate attendance & homework, level is 2
    result_med = calculate_what_if(karthik, attendance=85, homework=80)
    assert result_med["level"] == 2
    assert 20 <= result_med["score"] < 34

    # With poor attendance & homework, level is 3
    result_low = calculate_what_if(karthik, attendance=60, homework=50)
    assert result_low["level"] == 3
    assert result_low["score"] >= 34


def test_recompute_support_and_nightly_job(db_session: Session):
    """
    Verifies support snapshot computation and nightly job execution.
    """
    user = db_session.query(User).filter(User.email == "student@edupulse.demo").first()
    karthik = db_session.query(Student).filter(Student.user_id == user.id).first()

    snap = recompute_student_support(db_session, karthik.id)
    assert snap.level == 3
    assert snap.baseline == 73
    assert snap.drop == 9
    assert snap.minutes == 8
    assert snap.benefit == 95

    count = run_nightly_support_job(db_session)
    assert count >= 8


# =========================================================================
# 2. PLANNER ORDERING API TESTS
# =========================================================================

def test_planner_ordering_and_budgets(client: TestClient, db_session: Session):
    """
    Verifies benefit-per-minute ranking for budgets 10, 20, and 30 minutes.
    """
    token = get_teacher_token(db_session)
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Budget 10 min
    res10 = client.get("/api/v1/teacher/today?budget=10", headers=headers)
    assert res10.status_code == 200
    data10 = res10.json()
    assert data10["budget"] == 10
    assert data10["used"] <= 10
    in_plan_10_names = [s["name"] for s in data10["in_plan"]]
    assert "Vikram" in in_plan_10_names  # Vikram has highest benefit/min (12.0)

    # 2. Budget 20 min (matches prototype exactly: Karthik, Arun, Vikram with 19 min used)
    res20 = client.get("/api/v1/teacher/today?budget=20", headers=headers)
    assert res20.status_code == 200
    data20 = res20.json()
    assert data20["budget"] == 20
    assert data20["used"] == 19
    in_plan_20_names = [s["name"] for s in data20["in_plan"]]
    assert in_plan_20_names == ["Karthik", "Arun", "Vikram"]
    assert data20["in_plan"][0]["support_level"] == 3  # Karthik (sorted level desc)

    later_20_names = [s["name"] for s in data20["later"]]
    assert "Divya" in later_20_names
    assert "Rahul" in later_20_names

    bright_names = [b["name"] for b in data20["bright"]]
    assert "Meena" in bright_names
    assert "Sana" in bright_names

    # 3. Budget 30 min (used 24 min: Karthik 8, Arun 6, Vikram 5, Rahul 3, Lakshmi 2)
    res30 = client.get("/api/v1/teacher/today?budget=30", headers=headers)
    assert res30.status_code == 200
    data30 = res30.json()
    assert data30["budget"] == 30
    assert data30["used"] == 24
    in_plan_30_names = [s["name"] for s in data30["in_plan"]]
    assert "Karthik" in in_plan_30_names
    assert "Arun" in in_plan_30_names
    assert "Vikram" in in_plan_30_names
    assert "Rahul" in in_plan_30_names
    assert "Lakshmi" in in_plan_30_names
    # Divya needs 10 min, does not fit in remaining 6 min
    assert any(s["name"] == "Divya" for s in data30["later"])


# =========================================================================
# 3. PERMISSIONS & ROLE SCOPING TESTS
# =========================================================================

def test_student_forbidden_from_teacher_today(client: TestClient, db_session: Session):
    token = get_student_token(db_session)
    res = client.get("/api/v1/teacher/today", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 403


def test_parent_forbidden_from_teacher_today(client: TestClient, db_session: Session):
    token = get_parent_token(db_session)
    res = client.get("/api/v1/teacher/today", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 403


def test_teacher_forbidden_from_other_school_student(client: TestClient, db_session: Session):
    """
    A teacher cannot access a student belonging to a different school.
    """
    other_school = School(name="Other Trichy School")
    db_session.add(other_school)
    db_session.flush()

    other_user = User(
        school_id=other_school.id,
        role="teacher",
        name="Other Teacher",
        email="other.teacher@edupulse.demo",
        password_hash=get_password_hash("Demo@1234"),
    )
    db_session.add(other_user)
    db_session.commit()

    token = create_access_token(subject=other_user.id, role="teacher", school_id=other_school.id)

    karthik = db_session.query(Student).join(User).filter(User.email == "student@edupulse.demo").first()
    res = client.get(f"/api/v1/teacher/students/{karthik.id}", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code in (403, 404)


# =========================================================================
# 4. DIAGNOSTIC DETAIL, WHAT-IF, & PLAYBOOK ACTIONS TESTS
# =========================================================================

def test_teacher_student_detail(client: TestClient, db_session: Session):
    token = get_teacher_token(db_session)
    headers = {"Authorization": f"Bearer {token}"}

    karthik = db_session.query(Student).join(User).filter(User.email == "student@edupulse.demo").first()
    res = client.get(f"/api/v1/teacher/students/{karthik.id}", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["student"]["name"] == "Karthik"
    assert data["baseline"] in (73, 74)
    assert data["drop"] in (9, 14)
    assert len(data["tests"]) == 8
    assert len(data["chart_data"]) == 8


def test_teacher_what_if_endpoint(client: TestClient, db_session: Session):
    token = get_teacher_token(db_session)
    headers = {"Authorization": f"Bearer {token}"}

    karthik = db_session.query(Student).join(User).filter(User.email == "student@edupulse.demo").first()
    res = client.post(
        f"/api/v1/teacher/students/{karthik.id}/what-if",
        headers=headers,
        json={"attendance": 85, "homework": 80},
    )
    assert res.status_code == 200
    data = res.json()
    assert "level" in data
    assert "score" in data
    assert data["drop"] in (9, 14)


def test_teacher_playbook_action_logging(client: TestClient, db_session: Session):
    token = get_teacher_token(db_session)
    headers = {"Authorization": f"Bearer {token}"}

    karthik = db_session.query(Student).join(User).filter(User.email == "student@edupulse.demo").first()

    # Log action
    action_text = "5-minute parent call regarding fractions practice"
    post_res = client.post(
        f"/api/v1/teacher/students/{karthik.id}/actions",
        headers=headers,
        json={"action": action_text, "note": "Parent agreed to 10 min daily home practice."},
    )
    assert post_res.status_code == 200
    action_data = post_res.json()
    assert action_data["action"] == action_text
    assert action_data["followup_due"] is not None

    # Verify action appears in GET /actions
    get_res = client.get(f"/api/v1/teacher/students/{karthik.id}/actions", headers=headers)
    assert get_res.status_code == 200
    actions_list = get_res.json()
    assert any(a["action"] == action_text for a in actions_list)

    # Verify audit log
    audit_entry = (
        db_session.query(AuditLog)
        .filter(AuditLog.action == "LOG_PLAYBOOK_ACTION", AuditLog.entity_id == karthik.id)
        .first()
    )
    assert audit_entry is not None


# =========================================================================
# 5. PARENT NOTE DRAFT & APPROVAL WORKFLOW TESTS
# =========================================================================

def test_parent_note_draft_and_approval_workflow(client: TestClient, db_session: Session):
    token = get_teacher_token(db_session)
    headers = {"Authorization": f"Bearer {token}"}

    karthik = db_session.query(Student).join(User).filter(User.email == "student@edupulse.demo").first()

    # 1. GET Draft note
    draft_res = client.get(f"/api/v1/teacher/students/{karthik.id}/parent-note", headers=headers)
    assert draft_res.status_code == 200
    draft = draft_res.json()
    assert "Karthik has been working hard" in draft["body_en"]
    assert "அறிவியலில் கார்த்திக்" in draft["body_ta"]

    # 2. Approve and queue note
    approve_res = client.post(
        f"/api/v1/teacher/students/{karthik.id}/parent-note",
        headers=headers,
        json={
            "body_en": draft["body_en"],
            "body_ta": draft["body_ta"],
            "approved": True,
            "channel": "WhatsApp",
        },
    )
    assert approve_res.status_code == 200
    approve_data = approve_res.json()
    assert approve_data["status"] == "approved"
    assert approve_data["outbox_id"] is not None

    # 3. Check OutboxMessage created for Karthik's mother
    outbox_msg = db_session.query(OutboxMessage).filter(OutboxMessage.id == approve_data["outbox_id"]).first()
    assert outbox_msg is not None
    assert outbox_msg.channel == "whatsapp"
    assert outbox_msg.status == "queued"
    assert "student_name" in outbox_msg.payload


# =========================================================================
# 6. BRIGHT SPOTS & KUDOS TESTS
# =========================================================================

def test_bright_spots_and_kudos(client: TestClient, db_session: Session):
    token = get_teacher_token(db_session)
    headers = {"Authorization": f"Bearer {token}"}

    # 1. GET Bright Spots
    res = client.get("/api/v1/teacher/bright-spots", headers=headers)
    assert res.status_code == 200
    bright_list = res.json()
    names = [b["name"] for b in bright_list]
    assert "Meena" in names
    assert "Sana" in names

    meena = next(b for b in bright_list if b["name"] == "Meena")

    # 2. Send Kudos to Meena
    kudos_res = client.post(
        "/api/v1/teacher/kudos",
        headers=headers,
        json={"student_id": meena["id"], "message": "Incredible turnaround in test scores!"},
    )
    assert kudos_res.status_code == 200
    assert kudos_res.json()["success"] is True

    # 3. GET Bright Spots again -> kudos_sent should now be True
    res2 = client.get("/api/v1/teacher/bright-spots", headers=headers)
    bright_list2 = res2.json()
    meena2 = next(b for b in bright_list2 if b["name"] == "Meena")
    assert meena2["kudos_sent"] is True

    # 4. Verify Audit Log entry
    audit_entry = (
        db_session.query(AuditLog)
        .filter(AuditLog.action == "SEND_KUDOS", AuditLog.entity_id == meena["id"])
        .first()
    )
    assert audit_entry is not None
