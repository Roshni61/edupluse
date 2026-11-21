import pytest
from datetime import date, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.seed import seed_database
from app.core.rate_limiter import login_rate_limiter
from app.core.security import create_access_token
from app.models.models import (
    User,
    Student,
    Class,
    ParentLink,
    Booking,
    Checkin,
    ParentNote,
    CallbackQueue,
    OutboxMessage,
)
from app.services.reach import escalate_family, get_ladder_step


@pytest.fixture(autouse=True)
def setup_parent_test_env(db_session: Session):
    login_rate_limiter.reset()
    seed_database(db_session)
    yield
    login_rate_limiter.reset()


def get_token(user: User) -> str:
    return create_access_token(subject=user.id, role=user.role, school_id=user.school_id)


def test_parent_home_growth_only_and_latest_note(client: TestClient, db_session: Session):
    """
    PRODUCT RULE 3: Students and parents see growth only, never support level.
    GET /parent/home returns growth summary, latest approved note, and no support level.
    """
    parent_user = db_session.query(User).filter(User.email == "parent@edupulse.demo").first()
    assert parent_user is not None

    token = get_token(parent_user)
    res = client.get("/parent/home", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()

    assert "child" in data
    assert data["child"]["name"] == "Karthik"
    assert "growth_highlight" in data["child"]
    # Verify support level is NEVER exposed to parent
    assert "support_level" not in data["child"]
    assert "level" not in data["child"]

    # Check preferences
    assert "preferences" in data
    assert data["preferences"]["preferred_channel"] in ["whatsapp", "sms", "voice", "app", "callback", "desk"]


def test_evening_slot_on_wednesday_rejected(client: TestClient, db_session: Session):
    """
    PRODUCT RULE 5: Parent call windows stay inside school hours; evening slots only Tue and Thu.
    Booking an evening slot on a Wednesday must be rejected with HTTP 400.
    Booking an evening slot on a Tuesday must succeed.
    """
    parent_user = db_session.query(User).filter(User.email == "parent@edupulse.demo").first()
    assert parent_user is not None
    token = get_token(parent_user)

    # Attempt evening slot on Wednesday -> MUST FAIL
    res_wed = client.post(
        "/parent/bookings",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "day": "Wed",
            "window_id": "eve",
            "time": "6:30",
            "method": "call",
            "reminders": ["whatsapp", "hour"],
        },
    )
    assert res_wed.status_code == 400
    assert "Tuesday and Thursday" in res_wed.json()["detail"]

    # Attempt evening slot on Tuesday -> MUST SUCCEED
    res_tue = client.post(
        "/parent/bookings",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "day": "Tue",
            "window_id": "eve",
            "time": "6:30",
            "method": "call",
            "reminders": ["whatsapp", "hour"],
        },
    )
    assert res_tue.status_code == 201
    assert res_tue.json()["day"] == "Tue"
    assert res_tue.json()["time"] == "6:30"


def test_parent_booking_conflict_returns_409(client: TestClient, db_session: Session):
    """
    Ensures booking conflict handling:
    When a slot is already booked for that teacher and time, returns HTTP 409 Conflict.
    """
    parent1 = db_session.query(User).filter(User.email == "parent@edupulse.demo").first()
    assert parent1 is not None

    parent2 = db_session.query(User).filter(User.email == "divya.parent@edupulse.demo").first()
    if not parent2:
        parent2 = User(
            school_id=parent1.school_id,
            role="parent",
            name="Second Parent",
            email="parent2@edupulse.demo",
            password_hash="test",
            language="en",
            is_active=True,
        )
        db_session.add(parent2)
        db_session.commit()
        db_session.refresh(parent2)

    token1 = get_token(parent1)
    token2 = get_token(parent2)

    # Parent 1 books Tuesday 7:35 AM
    slot_time = "7:35"
    res1 = client.post(
        "/parent/bookings",
        headers={"Authorization": f"Bearer {token1}"},
        json={
            "day": "Tue",
            "window_id": "am",
            "time": slot_time,
            "method": "call",
            "reminders": ["whatsapp"],
        },
    )
    assert res1.status_code == 201

    # Parent 2 tries to book the EXACT SAME Tuesday 7:35 AM slot with same teacher
    res2 = client.post(
        "/parent/bookings",
        headers={"Authorization": f"Bearer {token2}"},
        json={
            "day": "Tue",
            "window_id": "am",
            "time": slot_time,
            "method": "call",
            "reminders": ["sms"],
        },
    )
    assert res2.status_code == 409
    assert "already booked" in res2.json()["detail"].lower() or "conflict" in res2.json()["detail"].lower()


def test_ics_validity_and_valarms(client: TestClient, db_session: Session):
    """
    GET /parent/bookings/{id}.ics returns a valid RFC 5545 iCalendar file
    with selected reminders serialized as VALARM components.
    """
    parent_user = db_session.query(User).filter(User.email == "parent@edupulse.demo").first()
    token = get_token(parent_user)

    # Book a call with multiple reminders
    res = client.post(
        "/parent/bookings",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "day": "Thu",
            "window_id": "lunch",
            "time": "1:05",
            "method": "call",
            "reminders": ["hour", "day", "five"],
        },
    )
    assert res.status_code == 201
    booking_id = res.json()["id"]

    # Request .ics file
    ics_res = client.get(f"/parent/bookings/{booking_id}.ics", headers={"Authorization": f"Bearer {token}"})
    assert ics_res.status_code == 200
    assert "text/calendar" in ics_res.headers.get("content-type", "")

    ics_content = ics_res.text
    assert "BEGIN:VCALENDAR" in ics_content
    assert "END:VCALENDAR" in ics_content
    assert "BEGIN:VEVENT" in ics_content
    assert "END:VEVENT" in ics_content
    assert "DTSTART:" in ics_content
    assert "DTEND:" in ics_content

    # Verify VALARM triggers for reminders
    assert "BEGIN:VALARM" in ics_content
    assert "TRIGGER:-PT1H" in ics_content
    assert "TRIGGER:-P1D" in ics_content
    assert "TRIGGER:-PT5M" in ics_content
    assert "END:VALARM" in ics_content


def test_parent_cannot_read_or_cancel_other_parent_booking(client: TestClient, db_session: Session):
    """
    Ownership guard: A parent cannot download .ics or cancel another parent's booking.
    """
    parent1 = db_session.query(User).filter(User.email == "parent@edupulse.demo").first()
    parent2 = db_session.query(User).filter(User.email == "divya.parent@edupulse.demo").first()
    assert parent1 is not None and parent2 is not None

    token1 = get_token(parent1)
    token2 = get_token(parent2)

    # Parent 1 creates a booking
    res1 = client.post(
        "/parent/bookings",
        headers={"Authorization": f"Bearer {token1}"},
        json={
            "day": "Mon",
            "window_id": "lunch",
            "time": "1:15",
            "method": "call",
            "reminders": ["whatsapp"],
        },
    )
    assert res1.status_code == 201
    booking_id = res1.json()["id"]

    # Parent 2 tries to download Parent 1's .ics -> FORBIDDEN
    res_ics = client.get(f"/parent/bookings/{booking_id}.ics", headers={"Authorization": f"Bearer {token2}"})
    assert res_ics.status_code == 403

    # Parent 2 tries to cancel Parent 1's booking -> FORBIDDEN
    res_del = client.delete(f"/parent/bookings/{booking_id}", headers={"Authorization": f"Bearer {token2}"})
    assert res_del.status_code == 403

    # Parent 1 cancels their own booking -> SUCCEEDS
    res_own_del = client.delete(f"/parent/bookings/{booking_id}", headers={"Authorization": f"Bearer {token1}"})
    assert res_own_del.status_code == 200


def test_reach_ladder_escalation_logic(client: TestClient, db_session: Session):
    """
    Reach ladder escalation:
    Moves a family one step down the reach ladder (1->2->3->4->5) when messages go unanswered.
    Stores each attempt in outbox_messages.
    Step 4 adds family to callback_queue.
    """
    student = db_session.query(Student).first()
    parent = db_session.query(User).filter(User.role == "parent").first()

    link = ParentLink(
        parent_user_id=parent.id,
        student_id=student.id,
        relation="Guardian",
        preferred_channel="whatsapp",
        preferred_language="ta",
        no_smartphone=False,
        shift_worker=False,
    )
    db_session.add(link)
    db_session.commit()
    db_session.refresh(link)

    # Initial: Step 1
    assert get_ladder_step(link.preferred_channel) == 1

    # Escalate to Step 2 (SMS)
    step2 = escalate_family(db_session, link, reason="2 weeks unread WhatsApp")
    assert step2 == 2
    assert link.preferred_channel == "sms"

    # Escalate to Step 3 (Automated Voice)
    step3 = escalate_family(db_session, link, reason="SMS reply timeout")
    assert step3 == 3
    assert link.preferred_channel == "voice"

    # Escalate to Step 4 (Teacher Callback) -> Enqueues to callback_queue
    step4 = escalate_family(db_session, link, reason="Voice call unanswered twice")
    assert step4 == 4
    assert link.preferred_channel == "callback"

    cb_entry = (
        db_session.query(CallbackQueue)
        .filter(CallbackQueue.student_id == student.id, CallbackQueue.status == "pending")
        .first()
    )
    assert cb_entry is not None

    # Escalate to Step 5 (School Desk, Saturday)
    step5 = escalate_family(db_session, link, reason="Teacher callback unanswered")
    assert step5 == 5
    assert link.preferred_channel == "desk"

    # Verify outbox messages recorded
    outbox_count = (
        db_session.query(OutboxMessage)
        .filter(OutboxMessage.to_user_id == parent.id, OutboxMessage.template == "reach_ladder_escalation")
        .count()
    )
    assert outbox_count >= 4


def test_sms_inbound_webhook(client: TestClient, db_session: Session):
    """
    POST /sms/inbound webhook:
    Reply code "1" -> acknowledged
    Reply code "2" -> enqueues to callback_queue
    """
    student = db_session.query(Student).first()
    parent = db_session.query(User).filter(User.role == "parent").first()

    # Inbound "1"
    res1 = client.post(
        "/sms/inbound",
        json={"from_phone": "+919876543210", "body": "1", "student_id": student.id, "parent_user_id": parent.id},
    )
    assert res1.status_code == 200
    assert res1.json()["action"] == "acknowledged_well"

    # Inbound "2"
    res2 = client.post(
        "/sms/inbound",
        json={"from_phone": "+919876543210", "body": "2", "student_id": student.id, "parent_user_id": parent.id},
    )
    assert res2.status_code == 200
    assert res2.json()["action"] == "callback_enqueued"

    # Verify callback_queue entry created
    cb = (
        db_session.query(CallbackQueue)
        .filter(CallbackQueue.student_id == student.id, CallbackQueue.reason.like("%SMS reply code '2'%"))
        .first()
    )
    assert cb is not None


def test_voice_simulate_endpoint(client: TestClient, db_session: Session):
    """
    POST /voice/simulate records automated voice simulator outcome.
    Keypad '2' triggers callback request.
    """
    parent = db_session.query(User).filter(User.role == "parent").first()
    token = get_token(parent)

    res = client.post(
        "/voice/simulate",
        headers={"Authorization": f"Bearer {token}"},
        json={"keypad_input": "2"},
    )
    assert res.status_code == 200
    assert res.json()["outcome"] == "callback_requested"


def test_teacher_connect_and_reserve_callback(client: TestClient, db_session: Session):
    """
    Teacher endpoints:
    GET /teacher/connect -> returns ladder counts, unreached families, and booked slots.
    POST /teacher/callbacks -> reserves a callback for an unreached family and dispatches notification.
    """
    teacher_user = db_session.query(User).filter(User.email == "teacher@edupulse.demo").first()
    token = get_token(teacher_user)

    # GET /teacher/connect
    res = client.get("/teacher/connect", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()
    assert "ladder" in data
    assert len(data["ladder"]) == 5
    assert "unreached" in data
    assert "booked" in data
    assert data["booked_count"] >= 4

    # POST /teacher/callbacks
    unreached_id = data["unreached"][0]["id"]
    cb_res = client.post(
        "/teacher/callbacks",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "callback_id": unreached_id,
            "day": "Thu",
            "time": "4:20",
            "method": "call",
        },
    )
    assert cb_res.status_code == 200
    assert cb_res.json()["success"] is True
    assert "booking_id" in cb_res.json()
