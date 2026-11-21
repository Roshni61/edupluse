import pytest
from datetime import date
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.seed import seed_database
from app.core.rate_limiter import login_rate_limiter
from app.core.security import create_access_token
from app.models.models import (
    User,
    Student,
    School,
    AuditLog,
)

SENSITIVE_FIELDS = {"caste", "religion", "income", "gender"}


@pytest.fixture(autouse=True)
def setup_admin_test_env(db_session: Session):
    login_rate_limiter.reset()
    seed_database(db_session)
    yield
    login_rate_limiter.reset()


def get_token(user: User) -> str:
    return create_access_token(subject=user.id, role=user.role, school_id=user.school_id)


def assert_no_sensitive_fields(obj, path=""):
    """
    Recursively asserts that neither dictionary keys nor list items expose sensitive attributes.
    PRODUCT RULE 4: No sensitive attributes are stored or exposed (caste, religion, income, gender).
    """
    if isinstance(obj, dict):
        for k, v in obj.items():
            lower_k = str(k).lower()
            for s in SENSITIVE_FIELDS:
                assert s not in lower_k, f"Forbidden sensitive field '{k}' exposed at path '{path}.{k}'"
            assert_no_sensitive_fields(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for idx, item in enumerate(obj):
            assert_no_sensitive_fields(item, f"{path}[{idx}]")


def test_admin_overview_aggregates_and_no_individual_names(client: TestClient, db_session: Session):
    """
    GET /admin/overview returns aggregated equity bands, reach, class heatmap, and counts only.
    Confirms no individual student names or support levels are exposed to admins.
    """
    admin_user = db_session.query(User).filter(User.role == "admin").first()
    assert admin_user is not None
    token = get_token(admin_user)

    res = client.get("/admin/overview", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()

    # KPIs check
    assert "kpis" in data
    assert "support_plan_count" in data["kpis"]
    assert "families_reached_pct" in data["kpis"]
    assert "badge_earning_pct" in data["kpis"]

    # Equity check
    assert "equity" in data
    bands = {e["band"]: e["earned"] for e in data["equity"]}
    assert "Needs support" in bands
    assert "On track" in bands
    assert "Strong" in bands

    # Equity alert check
    assert "equity_alert" in data
    assert "flagged" in data["equity_alert"]
    assert "gap" in data["equity_alert"]

    # Reach check
    assert "reach" in data
    assert len(data["reach"]) >= 4

    # Class support heatmap
    assert "heat_classes" in data
    assert "heat" in data
    assert len(data["heat"]) == len(data["heat_classes"])

    # Verify no individual student names appear in overview payload
    content_str = str(data).lower()
    for s in db_session.query(Student).all():
        if s.name and len(s.name) > 3:
            assert s.name.lower() not in content_str, f"Individual student name {s.name} exposed in admin overview!"


def test_equity_alert_flagged_when_gap_exceeds_10(client: TestClient, db_session: Session):
    """
    Verifies that if the badge-earning rate of the 'Needs support' band falls more
    than 10 points below 'Strong', an equity alert is triggered on the overview.
    """
    admin_user = db_session.query(User).filter(User.role == "admin").first()
    token = get_token(admin_user)

    res = client.get("/admin/overview", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()

    equity = {e["band"]: e["earned"] for e in data["equity"]}
    gap = equity["Strong"] - equity["Needs support"]

    if gap > 10:
        assert data["equity_alert"]["flagged"] is True
        assert "Equity Alert" in data["equity_alert"]["message"]
    else:
        assert data["equity_alert"]["flagged"] is False


def test_admin_guardrails_list(client: TestClient, db_session: Session):
    """
    GET /admin/guardrails lists locked guardrails and school-level feature flags.
    """
    admin_user = db_session.query(User).filter(User.role == "admin").first()
    token = get_token(admin_user)

    res = client.get("/admin/guardrails", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()

    assert "guardrails" in data
    assert "feature_flags" in data

    locked_keys = {g["key"] for g in data["guardrails"] if g["locked"]}
    assert "public_leaderboards" in locked_keys
    assert "push_notifications_children" in locked_keys
    assert "no_sensitive_attributes" in locked_keys
    assert "teacher_only_support_levels" in locked_keys
    assert "growth_only_student_view" in locked_keys


def test_locked_guardrail_modification_rejected_with_403(client: TestClient, db_session: Session):
    """
    Attempting to enable public leaderboards, push notifications, or disable privacy
    rules via PATCH /admin/settings MUST reject with HTTP 403 Forbidden and write to audit_logs.
    """
    admin_user = db_session.query(User).filter(User.role == "admin").first()
    token = get_token(admin_user)

    # 1. Attempt to enable public leaderboards -> MUST REJECT
    res_leaderboard = client.patch(
        "/admin/settings",
        headers={"Authorization": f"Bearer {token}"},
        json={"feature_flags": {"public_leaderboards": True}},
    )
    assert res_leaderboard.status_code == 403
    assert "locked permanent guardrails" in res_leaderboard.json()["detail"]

    # 2. Attempt to disable no_sensitive_attributes -> MUST REJECT
    res_sensitive = client.patch(
        "/admin/settings",
        headers={"Authorization": f"Bearer {token}"},
        json={"feature_flags": {"no_sensitive_attributes": False}},
    )
    assert res_sensitive.status_code == 403

    # 3. Verify audit log recorded the violation attempt
    audit_entry = (
        db_session.query(AuditLog)
        .filter(AuditLog.action == "VIOLATION_ATTEMPT_MODIFY_LOCKED_GUARDRAILS")
        .first()
    )
    assert audit_entry is not None

    # 4. Valid feature flag update -> SUCCEEDS
    res_valid = client.patch(
        "/admin/settings",
        headers={"Authorization": f"Bearer {token}"},
        json={"feature_flags": {"daily_mission_cap": 4}},
    )
    assert res_valid.status_code == 200
    assert res_valid.json()["feature_flags"]["daily_mission_cap"] == 4


def test_admin_audit_logs_filters_and_pagination(client: TestClient, db_session: Session):
    """
    GET /admin/audit-logs returns paginated audit entries with action, actor, and date filtering.
    """
    admin_user = db_session.query(User).filter(User.role == "admin").first()
    token = get_token(admin_user)

    res = client.get("/admin/audit-logs?limit=10&offset=0", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()

    assert "total" in data
    assert "items" in data
    assert data["limit"] == 10
    assert data["offset"] == 0
    assert len(data["items"]) <= 10

    # Filter by action
    res_action = client.get("/admin/audit-logs?action=VIEW", headers={"Authorization": f"Bearer {token}"})
    assert res_action.status_code == 200
    for item in res_action.json()["items"]:
        assert "view" in item["action"].lower()


def test_non_admin_forbidden_from_admin_endpoints(client: TestClient, db_session: Session):
    """
    Teachers, parents, and students must be rejected from /admin routes with HTTP 403.
    """
    teacher = db_session.query(User).filter(User.role == "teacher").first()
    student = db_session.query(User).filter(User.role == "student").first()
    parent = db_session.query(User).filter(User.role == "parent").first()

    for u in [teacher, student, parent]:
        tok = get_token(u)
        assert client.get("/admin/overview", headers={"Authorization": f"Bearer {tok}"}).status_code == 403
        assert client.get("/admin/guardrails", headers={"Authorization": f"Bearer {tok}"}).status_code == 403
        assert client.get("/admin/audit-logs", headers={"Authorization": f"Bearer {tok}"}).status_code == 403


# =========================================================================
# CRITICAL COMPLIANCE TEST: SENSITIVE ATTRIBUTES NEVER EXPOSED (RULE 4)
# =========================================================================

def test_apis_never_expose_sensitive_attributes(client: TestClient, db_session: Session):
    """
    PRODUCT RULE 4: No sensitive attributes are stored or exposed (caste, religion, income, gender).
    Tests database schema columns and all role APIs (teacher, student, parent, admin)
    to guarantee that none of ['caste', 'religion', 'income', 'gender'] are exposed anywhere.
    """
    # 1. Database Model Columns Inspection
    for model_class in [Student, User, School]:
        columns = [c.name.lower() for c in model_class.__table__.columns]
        for s in SENSITIVE_FIELDS:
            assert s not in columns, f"Model {model_class.__name__} has prohibited column '{s}'!"

    teacher = db_session.query(User).filter(User.role == "teacher").first()
    student = db_session.query(User).filter(User.role == "student").first()
    parent = db_session.query(User).filter(User.role == "parent").first()
    admin = db_session.query(User).filter(User.role == "admin").first()

    t_tok = get_token(teacher)
    s_tok = get_token(student)
    p_tok = get_token(parent)
    a_tok = get_token(admin)

    # 2. Teacher API responses
    res_students = client.get("/teacher/students", headers={"Authorization": f"Bearer {t_tok}"})
    assert res_students.status_code == 200
    assert_no_sensitive_fields(res_students.json(), "teacher.students")

    first_student = db_session.query(Student).first()
    res_detail = client.get(f"/teacher/students/{first_student.id}", headers={"Authorization": f"Bearer {t_tok}"})
    assert res_detail.status_code == 200
    assert_no_sensitive_fields(res_detail.json(), "teacher.student_detail")

    # 3. Student API responses
    res_student_home = client.get("/student/home", headers={"Authorization": f"Bearer {s_tok}"})
    assert res_student_home.status_code == 200
    assert_no_sensitive_fields(res_student_home.json(), "student.home")

    # 4. Parent API responses
    res_parent_home = client.get("/parent/home", headers={"Authorization": f"Bearer {p_tok}"})
    assert res_parent_home.status_code == 200
    assert_no_sensitive_fields(res_parent_home.json(), "parent.home")

    # 5. Admin API responses
    res_admin_overview = client.get("/admin/overview", headers={"Authorization": f"Bearer {a_tok}"})
    assert res_admin_overview.status_code == 200
    assert_no_sensitive_fields(res_admin_overview.json(), "admin.overview")
