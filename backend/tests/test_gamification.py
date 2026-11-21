import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.db.seed import seed_database
from app.core.rate_limiter import login_rate_limiter
from app.core.security import create_access_token
from app.models.models import (
    User,
    Student,
    Mission,
    MissionAttempt,
    GardenDrop,
    Doubt,
    XpLedger,
    Badge,
    StudentBadge,
)


@pytest.fixture(autouse=True)
def setup_gamification_test_env(db_session: Session):
    login_rate_limiter.reset()
    seed_database(db_session)
    yield
    login_rate_limiter.reset()


def get_token_for(db_session: Session, email: str, role: str) -> str:
    user = db_session.query(User).filter(User.email == email).first()
    return create_access_token(subject=user.id, role=role, school_id=user.school_id)


# =========================================================================
# 1. PRODUCT RULE 1: SAME EFFORT GIVES SAME XP FOR WEAK AND STRONG STUDENTS
# =========================================================================

def test_same_effort_same_xp_for_weak_and_strong_students(client: TestClient, db_session: Session):
    """
    PRODUCT RULE 1: Effort over Marks.
    XP is awarded for completing the mission, never for marks.
    A struggling student (score 40%, 3 hints) receives the exact same XP
    as a high-scoring student (score 100%, 0 hints).
    """
    karthik_user = db_session.query(User).filter(User.email == "student@edupulse.demo").first()
    karthik = db_session.query(Student).filter(Student.user_id == karthik_user.id).first()
    karthik_token = create_access_token(subject=karthik_user.id, role="student", school_id=karthik_user.school_id)

    divya_user = db_session.query(User).filter(User.email == "divya@edupulse.demo").first()
    divya = db_session.query(Student).filter(Student.user_id == divya_user.id).first()
    divya_token = create_access_token(subject=divya_user.id, role="student", school_id=divya_user.school_id)

    mission = db_session.query(Mission).filter(Mission.title == "Fraction warm-up").first()
    assert mission is not None
    mission_xp = mission.xp

    # Clear prior attempts for m1 if any
    db_session.query(MissionAttempt).filter(MissionAttempt.mission_id == mission.id).delete()
    db_session.commit()

    # Karthik struggles: uses 2 hints, scores 40
    res_karthik = client.post(
        f"/api/v1/student/missions/{mission.id}/submit",
        headers={"Authorization": f"Bearer {karthik_token}"},
        json={"hints_used": 2, "tries": 3, "score": 40},
    )
    assert res_karthik.status_code == 200
    data_karthik = res_karthik.json()

    # Divya scores 100 with 0 hints
    res_divya = client.post(
        f"/api/v1/student/missions/{mission.id}/submit",
        headers={"Authorization": f"Bearer {divya_token}"},
        json={"hints_used": 0, "tries": 1, "score": 100},
    )
    assert res_divya.status_code == 200
    data_divya = res_divya.json()

    # Both students must receive the exact same XP for their effort
    assert data_karthik["xp_awarded"] == mission_xp
    assert data_divya["xp_awarded"] == mission_xp
    assert data_karthik["xp_awarded"] == data_divya["xp_awarded"]


# =========================================================================
# 2. DOUBLE-SUBMIT SAFE (IDEMPOTENCY)
# =========================================================================

def test_double_submit_safe(client: TestClient, db_session: Session):
    """
    Finishing a mission twice never double-awards XP or duplicate garden drops.
    """
    user = db_session.query(User).filter(User.email == "student@edupulse.demo").first()
    token = create_access_token(subject=user.id, role="student", school_id=user.school_id)
    student = db_session.query(Student).filter(Student.user_id == user.id).first()

    mission = db_session.query(Mission).filter(Mission.title == "Explain it to a friend").first()
    db_session.query(MissionAttempt).filter(
        MissionAttempt.student_id == student.id,
        MissionAttempt.mission_id == mission.id,
    ).delete()
    db_session.commit()

    initial_xp = student.current_xp

    # First submit -> awards mission.xp
    res1 = client.post(
        f"/api/v1/student/missions/{mission.id}/submit",
        headers={"Authorization": f"Bearer {token}"},
        json={"hints_used": 0, "tries": 1},
    )
    assert res1.status_code == 200
    assert res1.json()["xp_awarded"] == mission.xp
    assert res1.json()["already_completed"] is False
    assert student.current_xp == initial_xp + mission.xp

    # Second submit of same mission -> 0 XP awarded, already_completed is True
    res2 = client.post(
        f"/api/v1/student/missions/{mission.id}/submit",
        headers={"Authorization": f"Bearer {token}"},
        json={"hints_used": 0, "tries": 1},
    )
    assert res2.status_code == 200
    assert res2.json()["xp_awarded"] == 0
    assert res2.json()["already_completed"] is True
    # XP in database remains unchanged
    assert student.current_xp == initial_xp + mission.xp


# =========================================================================
# 3. PRODUCT RULE 6: ANONYMOUS DOUBTS NEVER LEAK IDENTITY
# =========================================================================

def test_doubts_endpoint_never_leaks_identity(client: TestClient, db_session: Session):
    """
    PRODUCT RULE 6: Anonymous "I'm stuck"/doubt questions must not be linkable
    to a student in teacher APIs.
    """
    student_user = db_session.query(User).filter(User.email == "student@edupulse.demo").first()
    student_token = create_access_token(subject=student_user.id, role="student", school_id=student_user.school_id)

    teacher_user = db_session.query(User).filter(User.email == "teacher@edupulse.demo").first()
    teacher_token = create_access_token(subject=teacher_user.id, role="teacher", school_id=teacher_user.school_id)

    doubt_text = "Fractions: I don't understand how cross-multiplication works"

    # Student posts doubt
    post_res = client.post(
        "/api/v1/student/doubts",
        headers={"Authorization": f"Bearer {student_token}"},
        json={"text": doubt_text, "topic": "Fractions"},
    )
    assert post_res.status_code == 200

    # 1. Verify Database Model: No student_id or user_id column
    doubt_db = db_session.query(Doubt).filter(Doubt.text.contains("cross-multiplication")).first()
    assert doubt_db is not None
    assert not hasattr(doubt_db, "student_id")
    assert not hasattr(doubt_db, "user_id")

    # 2. Verify Teacher API: Response contains zero student identifiers
    teacher_res = client.get("/api/v1/teacher/doubts", headers={"Authorization": f"Bearer {teacher_token}"})
    assert teacher_res.status_code == 200
    doubts = teacher_res.json()
    assert len(doubts) >= 1

    matched = next((d for d in doubts if "cross-multiplication" in d["text"]), None)
    assert matched is not None
    assert "student_id" not in matched
    assert "user_id" not in matched
    assert "student_name" not in matched
    assert "author" not in matched
    assert "roll_no" not in matched


# =========================================================================
# 4. PERMISSIONS: STUDENT CANNOT ACCESS TEACHER ENDPOINTS
# =========================================================================

def test_student_cannot_access_teacher_endpoints(client: TestClient, db_session: Session):
    token = get_token_for(db_session, "student@edupulse.demo", "student")
    headers = {"Authorization": f"Bearer {token}"}

    # Cannot access today plan
    assert client.get("/api/v1/teacher/today", headers=headers).status_code == 403
    # Cannot access diagnostic students list
    assert client.get("/api/v1/teacher/students", headers=headers).status_code == 403
    # Cannot access teacher missions management
    assert client.get("/api/v1/teacher/missions", headers=headers).status_code == 403
    assert client.post("/api/v1/teacher/missions", json={"mission_id": "m1", "assign": True}, headers=headers).status_code == 403
    # Cannot access teacher doubts
    assert client.get("/api/v1/teacher/doubts", headers=headers).status_code == 403


# =========================================================================
# 5. STUDENT HOME & GAMIFICATION PROGRESS
# =========================================================================

def test_student_home_growth_only_and_level_progress(client: TestClient, db_session: Session):
    """
    GET /student/home: XP total, level name/progress (Sprout/Sapling/Bloom/Grove),
    assigned missions, earned badges, class garden count, recent kudos.
    Never returns support level or class rankings.
    """
    token = get_token_for(db_session, "student@edupulse.demo", "student")
    res = client.get("/api/v1/student/home", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()

    assert "xp_total" in data
    assert data["xp_total"] >= 340  # Karthik's derived XP
    assert data["level_name"] in ("Sprout", "Sapling", "Bloom", "Grove")
    assert len(data["assigned_missions"]) >= 1
    assert "class_garden" in data
    assert "own_progress" in data

    # Critical compliance checks
    assert "support_level" not in data
    assert "reasons" not in data
    assert "rank" not in data
    assert "leaderboard" not in data


# =========================================================================
# 6. TEACHER SIDE MISSION MANAGEMENT & LOW-TECH TICKING
# =========================================================================

def test_teacher_missions_management_and_tick(client: TestClient, db_session: Session):
    teacher_token = get_token_for(db_session, "teacher@edupulse.demo", "teacher")
    headers = {"Authorization": f"Bearer {teacher_token}"}

    karthik = db_session.query(Student).join(User).filter(User.email == "student@edupulse.demo").first()
    mission = db_session.query(Mission).filter(Mission.title == "Ask one doubt").first()

    # Clear prior attempts for m3
    db_session.query(MissionAttempt).filter(
        MissionAttempt.student_id == karthik.id,
        MissionAttempt.mission_id == mission.id,
    ).delete()
    db_session.commit()

    # 1. GET /teacher/missions
    res_list = client.get("/api/v1/teacher/missions", headers=headers)
    assert res_list.status_code == 200
    missions = res_list.json()
    assert len(missions) >= 3

    # 2. Toggle assign
    res_assign = client.post(
        "/api/v1/teacher/missions",
        headers=headers,
        json={"mission_id": mission.id, "assign": True},
    )
    assert res_assign.status_code == 200

    # 3. Tick paper mission for student without device
    initial_xp = karthik.current_xp
    res_tick = client.post(
        f"/api/v1/teacher/missions/{mission.id}/tick",
        headers=headers,
        json={"student_id": karthik.id, "note": "Karthik did it on worksheet"},
    )
    assert res_tick.status_code == 200
    tick_data = res_tick.json()
    assert tick_data["success"] is True
    assert tick_data["xp_awarded"] == mission.xp
    assert karthik.current_xp == initial_xp + mission.xp

    # 4. Print cards
    res_cards = client.get("/api/v1/teacher/print-cards", headers=headers)
    assert res_cards.status_code == 200
    assert len(res_cards.json()) >= 1
