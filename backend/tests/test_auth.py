import pytest
from app.core.config import settings
from app.core.rate_limiter import login_rate_limiter
from app.core.security import get_password_hash, create_access_token
from app.models.models import User, Class, ClassTeacher, Student, School


@pytest.fixture(autouse=True)
def reset_rate_limiter():
    login_rate_limiter.reset()
    yield
    login_rate_limiter.reset()


# --------------------------------------------------------------------------
# 1. Login & Token Verification
# --------------------------------------------------------------------------

def test_login_success(client, seed_data):
    res = client.post(
        "/api/v1/auth/login",
        json={"email": "teacher@test.com", "password": "pass"},
    )
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert data["expires_in"] == 900
    assert data["user"]["email"] == "teacher@test.com"
    assert data["user"]["role"] == "teacher"
    assert data["user"]["school_id"] == "sch-1"


def test_login_invalid_password(client, seed_data):
    res = client.post(
        "/api/v1/auth/login",
        json={"email": "teacher@test.com", "password": "wrong-password"},
    )
    assert res.status_code == 401
    assert "incorrect email or password" in res.json()["detail"].lower()


def test_login_inactive_user(client, db_session, seed_data):
    inactive = User(
        id="usr-inactive",
        school_id="sch-1",
        name="Inactive Person",
        email="inactive@test.com",
        password_hash=get_password_hash("pass"),
        role="teacher",
        is_active=False,
    )
    db_session.add(inactive)
    db_session.commit()

    res = client.post(
        "/api/v1/auth/login",
        json={"email": "inactive@test.com", "password": "pass"},
    )
    assert res.status_code == 403
    assert "inactive" in res.json()["detail"].lower()


# --------------------------------------------------------------------------
# 2. Rate Limiting (5 attempts / min / IP)
# --------------------------------------------------------------------------

def test_login_rate_limiting(client, seed_data):
    # Perform 5 failed attempts (allowed)
    for _ in range(5):
        res = client.post(
            "/api/v1/auth/login",
            json={"email": "teacher@test.com", "password": "wrong"},
        )
        assert res.status_code == 401

    # 6th attempt should be blocked by rate limiter
    res6 = client.post(
        "/api/v1/auth/login",
        json={"email": "teacher@test.com", "password": "pass"},
    )
    assert res6.status_code == 429
    assert "too many login attempts" in res6.json()["detail"].lower()


# --------------------------------------------------------------------------
# 3. Refresh Token & Rotation
# --------------------------------------------------------------------------

def test_refresh_token_lifecycle(client, seed_data):
    # 1. Login to get tokens
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "teacher@test.com", "password": "pass"},
    )
    refresh_token = login_res.json()["refresh_token"]

    # 2. Use refresh token to obtain a new access token
    ref_res = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert ref_res.status_code == 200
    ref_data = ref_res.json()
    assert "access_token" in ref_data
    assert "refresh_token" in ref_data
    assert ref_data["token_type"] == "bearer"

    # 3. Old refresh token was rotated/revoked, cannot be reused
    reuse_res = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert reuse_res.status_code == 401


def test_refresh_with_invalid_token(client):
    res = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": "garbage.invalid.token"},
    )
    assert res.status_code == 401


# --------------------------------------------------------------------------
# 4. Logout & Invalidation
# --------------------------------------------------------------------------

def test_logout_invalidates_access_token(client, seed_data):
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "teacher@test.com", "password": "pass"},
    )
    access_token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    # Verify access token works
    me_res = client.get("/api/v1/auth/me", headers=headers)
    assert me_res.status_code == 200

    # Logout
    logout_res = client.post("/api/v1/auth/logout", headers=headers)
    assert logout_res.status_code == 200

    # Subsequent request with revoked token should fail
    me_after = client.get("/api/v1/auth/me", headers=headers)
    assert me_after.status_code == 401


# --------------------------------------------------------------------------
# 5. GET /auth/me
# --------------------------------------------------------------------------

def test_get_me(client, teacher_token):
    headers = {"Authorization": f"Bearer {teacher_token}"}
    res = client.get("/api/v1/auth/me", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["email"] == "teacher@test.com"
    assert data["role"] == "teacher"
    assert data["school_id"] == "sch-1"


# --------------------------------------------------------------------------
# 6. Forbidden Cross-Access Tests
# --------------------------------------------------------------------------

def test_parent_forbidden_from_viewing_other_parent_child(client, other_parent_token):
    """OWNERSHIP GUARD: Parent cannot view another student's record."""
    headers = {"Authorization": f"Bearer {other_parent_token}"}
    res = client.get("/api/v1/students/parent/child/stu-1", headers=headers)
    assert res.status_code == 403
    assert "parents may only access records for their own child" in res.json()["detail"].lower()


def test_student_forbidden_from_reading_teacher_endpoints(client, student_token):
    """OWNERSHIP GUARD: Student forbidden from reading teacher support view."""
    headers = {"Authorization": f"Bearer {student_token}"}
    res = client.get("/api/v1/students/teacher-view?class_name=9A", headers=headers)
    assert res.status_code == 403
    assert "not authorized" in res.json()["detail"].lower()


def test_student_forbidden_from_reading_other_student_detail(client, student_token):
    """OWNERSHIP GUARD: Student forbidden from reading individual student detail."""
    headers = {"Authorization": f"Bearer {student_token}"}
    res = client.get("/api/v1/students/stu-1", headers=headers)
    assert res.status_code == 403


def test_teacher_forbidden_from_reading_other_school(client, db_session, seed_data):
    """OWNERSHIP GUARD: Teacher in school 2 forbidden from accessing student in school 1."""
    # Teacher in School 2
    t2 = User(
        id="usr-teacher-sch2",
        school_id="sch-2",
        name="School 2 Teacher",
        email="t2@test.com",
        password_hash=get_password_hash("pass"),
        role="teacher",
    )
    db_session.add(t2)
    db_session.commit()

    t2_token = create_access_token(subject=t2.id, role="teacher", school_id="sch-2")
    headers = {"Authorization": f"Bearer {t2_token}"}

    # Attempt to read student stu-1 from sch-1
    res = client.get("/api/v1/students/stu-1", headers=headers)
    assert res.status_code == 403
    assert "different school" in res.json()["detail"].lower()


def test_teacher_forbidden_from_class_they_do_not_teach(client, db_session, seed_data):
    """OWNERSHIP GUARD: Teacher only accesses students in classes they teach."""
    # Teacher in School 1 who teaches 10B (not 9A)
    cls_10b = Class(id="cls-10b", school_id="sch-1", name="10B", grade="10")
    t_other = User(
        id="usr-teacher-10b",
        school_id="sch-1",
        name="Class 10 Teacher",
        email="t10@test.com",
        password_hash=get_password_hash("pass"),
        role="teacher",
    )
    db_session.add_all([cls_10b, t_other])
    db_session.commit()

    ct = ClassTeacher(id="ct-10b", class_id="cls-10b", teacher_id="usr-teacher-10b", subject="Physics")
    db_session.add(ct)
    db_session.commit()

    token_10b = create_access_token(subject=t_other.id, role="teacher", school_id="sch-1")
    headers = {"Authorization": f"Bearer {token_10b}"}

    # Attempt to read stu-1 (who belongs to 9A)
    res = client.get("/api/v1/students/stu-1", headers=headers)
    assert res.status_code == 403
    assert "classes they teach" in res.json()["detail"].lower()


def test_admin_forbidden_from_individual_student_detail(client, admin_token):
    """
    OWNERSHIP GUARD: Admin only aggregates and school settings (no individual student detail).
    """
    headers = {"Authorization": f"Bearer {admin_token}"}
    res = client.get("/api/v1/students/stu-1", headers=headers)
    assert res.status_code == 403
    assert "aggregates and settings" in res.json()["detail"].lower()


# --------------------------------------------------------------------------
# 7. Demo Reset Endpoint Tests
# --------------------------------------------------------------------------

def test_demo_reset_by_admin(client, admin_token):
    """Admin can reset demo data."""
    headers = {"Authorization": f"Bearer {admin_token}"}
    res = client.post("/api/v1/demo/reset", headers=headers)
    assert res.status_code == 200
    assert res.json()["success"] is True

    # Root route /demo/reset also works
    res_root = client.post("/demo/reset", headers=headers)
    assert res_root.status_code == 200
    assert res_root.json()["success"] is True


def test_demo_reset_forbidden_for_non_admin(client, teacher_token, student_token):
    """Teacher and Student forbidden from resetting demo."""
    res_t = client.post("/api/v1/demo/reset", headers={"Authorization": f"Bearer {teacher_token}"})
    assert res_t.status_code == 403

    res_s = client.post("/api/v1/demo/reset", headers={"Authorization": f"Bearer {student_token}"})
    assert res_s.status_code == 403


def test_demo_reset_disabled_in_production(client, admin_token, monkeypatch):
    """Demo reset returns 403 when DEMO_MODE is False or ENVIRONMENT is production."""
    monkeypatch.setattr(settings, "DEMO_MODE", False)
    headers = {"Authorization": f"Bearer {admin_token}"}
    res = client.post("/api/v1/demo/reset", headers=headers)
    assert res.status_code == 403
    assert "disabled in production" in res.json()["detail"].lower()
