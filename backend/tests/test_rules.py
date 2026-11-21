import pytest
from app.models.models import AuditLog, AnonymousDoubt, Student


# ---------------------------------------------------------
# PRODUCT RULE 1: XP is awarded for effort, never for marks
# ---------------------------------------------------------
def test_rule1_xp_awarded_for_effort_not_marks(client, student_token, seed_data):
    # Student completes mission after 1 try
    headers = {"Authorization": f"Bearer {student_token}"}
    res1 = client.post(
        "/api/v1/missions/complete",
        json={"mission_id": "m1", "tries": 1},
        headers=headers,
    )
    assert res1.status_code == 200
    # Mission m1 gives 30 XP
    assert res1.json()["xp_awarded"] == 30
    assert res1.json()["new_total_xp"] == 130  # Initial 100 + 30


# ---------------------------------------------------------
# PRODUCT RULE 2: No leaderboards. Class Garden is cooperative
# ---------------------------------------------------------
def test_rule2_garden_cooperative_and_anonymous(client, student_token):
    headers = {"Authorization": f"Bearer {student_token}"}
    res = client.get("/api/v1/garden/9A", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "total_drops" in data
    assert "stage" in data
    # Must NOT have individual student names or leaderboard
    assert "students" not in data
    assert "leaderboard" not in data


# ---------------------------------------------------------
# PRODUCT RULE 3: Students see growth only, never support level
# ---------------------------------------------------------
def test_rule3_student_sees_growth_only(client, student_token):
    headers = {"Authorization": f"Bearer {student_token}"}
    res = client.get("/api/v1/students/growth", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "current_xp" in data
    assert "baseline_score" in data
    # Critical: support level must NOT be visible to student
    assert "support_level" not in data
    assert "reasons" not in data


def test_rule3_student_forbidden_from_teacher_support_level_endpoint(client, student_token):
    """ENGINEERING RULE: Permission-denied test."""
    headers = {"Authorization": f"Bearer {student_token}"}
    res = client.get("/api/v1/students/teacher-view?class_name=9A", headers=headers)
    assert res.status_code == 403
    assert "not authorized" in res.json()["detail"].lower()


# ---------------------------------------------------------
# PRODUCT RULE 5: Parent call windows inside school hours; evening Tue/Thu only
# ---------------------------------------------------------
def test_rule5_parent_call_windows_valid_tue_evening(client, parent_token):
    headers = {"Authorization": f"Bearer {parent_token}"}
    res = client.post(
        "/api/v1/bookings",
        json={
            "day": "Tue",
            "window_id": "eve",
            "slot_time": "6:30",
            "method": "Phone call",
            "reminders": ["whatsapp"],
        },
        headers=headers,
    )
    assert res.status_code == 201
    assert res.json()["day"] == "Tue"
    assert res.json()["slot_time"] == "6:30"


def test_rule5_parent_call_windows_invalid_wed_evening(client, parent_token):
    headers = {"Authorization": f"Bearer {parent_token}"}
    res = client.post(
        "/api/v1/bookings",
        json={
            "day": "Wed",  # Wednesday evening is not allowed
            "window_id": "eve",
            "slot_time": "6:30",
            "method": "Phone call",
            "reminders": [],
        },
        headers=headers,
    )
    assert res.status_code == 400
    assert "only offered on tuesday and thursday" in res.json()["detail"].lower()


# ---------------------------------------------------------
# PRODUCT RULE 6: Anonymous doubts not linkable to a student
# ---------------------------------------------------------
def test_rule6_anonymous_doubt_unlinked(client, student_token, teacher_token, db_session):
    # Student submits doubt
    student_headers = {"Authorization": f"Bearer {student_token}"}
    res = client.post(
        "/api/v1/doubts",
        json={"class_name": "9A", "topic": "Fractions", "message": "I get stuck with common denominator"},
        headers=student_headers,
    )
    assert res.status_code == 201

    # Teacher reads doubts
    teacher_headers = {"Authorization": f"Bearer {teacher_token}"}
    res_t = client.get("/api/v1/doubts/9A", headers=teacher_headers)
    assert res_t.status_code == 200
    doubts = res_t.json()
    assert len(doubts) >= 1
    # Check that neither student_id, student_name, nor user_id is present
    for d in doubts:
        assert "student_id" not in d
        assert "student_name" not in d
        assert "user_id" not in d

    # Verify directly in DB that no student identity was persisted in doubt record
    db_doubt = db_session.query(AnonymousDoubt).filter(AnonymousDoubt.text.contains("Fractions")).first()
    assert db_doubt is not None
    assert not hasattr(db_doubt, "student_id")
    assert not hasattr(db_doubt, "user_id")


# ---------------------------------------------------------
# PRODUCT RULE 7: Sensitive read/write audited
# ---------------------------------------------------------
def test_rule7_teacher_access_logged_in_audit_log(client, teacher_token, db_session):
    headers = {"Authorization": f"Bearer {teacher_token}"}
    res = client.get("/api/v1/students/stu-1", headers=headers)
    assert res.status_code == 200

    # Verify audit log was created
    audit = db_session.query(AuditLog).filter(
        AuditLog.action == "READ_STUDENT_DETAIL",
        AuditLog.entity_id == "stu-1",
    ).first()
    assert audit is not None
    assert audit.meta.get("school_id") == "sch-1"
    assert audit.meta.get("actor_role") == "teacher"


# ---------------------------------------------------------
# ENGINEERING RULE: Parents see only their own child(ren)
# ---------------------------------------------------------
def test_parent_cannot_view_other_parent_child(client, other_parent_token):
    """Permission-denied: parent cannot view another student."""
    headers = {"Authorization": f"Bearer {other_parent_token}"}
    res = client.get("/api/v1/students/parent/child/stu-1", headers=headers)
    assert res.status_code == 403
    assert "parents may only access records for their own child" in res.json()["detail"].lower()


def test_parent_can_view_own_child(client, parent_token):
    headers = {"Authorization": f"Bearer {parent_token}"}
    res = client.get("/api/v1/students/parent/child/stu-1", headers=headers)
    assert res.status_code == 200
    assert res.json()["name"] == "Student Test"
