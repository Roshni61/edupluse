from typing import List, Optional, Dict, Any
from datetime import date, datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Response
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.api.deps import get_current_user, require_role
from app.db.session import get_db
from app.models.models import (
    User,
    Student,
    Class,
    ParentLink,
    Booking,
    Checkin,
    ParentNote,
    CallWindow,
)
from app.schemas.schemas import (
    ParentHomeResponse,
    ParentHomeChildSummary,
    ParentHomeNote,
    ParentBookingItem,
    ParentPreferencesResponse,
    ParentPreferencesUpdate,
    ParentCheckinCreate,
    ParentSlotsResponse,
    WindowSlots,
    ParentBookingCreate,
    InboundSMSRequest,
    VoiceSimulateRequest,
)
from app.services.booking_service import validate_booking_window, WINDOWS_CONFIG
from app.services.storage import get_storage_provider
from app.services.reach import process_inbound_sms, process_voice_simulation

router = APIRouter(prefix="/parent", tags=["Parent Portal"])

DAYS_LIST = ["Mon", "Tue", "Wed", "Thu", "Fri"]
DAYS_MAP = {"Mon": 0, "Tue": 1, "Wed": 2, "Thu": 3, "Fri": 4, "Sat": 5, "Sun": 6}


def get_parent_and_child(current_user: User, db: Session):
    link = db.query(ParentLink).filter(ParentLink.parent_user_id == current_user.id).first()
    if not link or not link.student:
        # Fallback for dev demo
        stu = db.query(Student).first()
        if not stu:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No child linked to parent account.")
        return None, stu
    return link, link.student


@router.get("/home", response_model=ParentHomeResponse)
def get_parent_home(
    current_user: User = Depends(require_role("parent")),
    db: Session = Depends(get_db),
):
    """
    PRODUCT RULE 3: Students and parents see growth only, never support level.
    Returns child growth summary, latest approved teacher note in preferred language,
    upcoming booking, and recent checkin status.
    """
    link, child = get_parent_and_child(current_user, db)

    # 1. Growth description
    growth = "Showing steady progress and active participation in class."
    if child.scores_list and len(child.scores_list) >= 2:
        diff = child.scores_list[-1] - child.scores_list[-2]
        if diff > 0:
            growth = f"Up {diff} marks on the latest {child.subject} assessment!"
        elif diff == 0:
            growth = f"Maintained steady marks in {child.subject}."
        else:
            growth = f"Working hard on foundational practice in {child.subject}."
    elif child.bright_why:
        growth = child.bright_why

    child_summary = ParentHomeChildSummary(
        id=child.id,
        name=child.name,
        class_name=child.class_name,
        roll_no=child.roll_no,
        subject=child.subject,
        attendance_pct=child.attendance_pct,
        homework_pct=child.homework_pct,
        current_xp=child.current_xp,
        growth_highlight=growth,
    )

    # 2. Latest approved teacher note
    pref_lang = link.preferred_language if link else (current_user.language or "ta")
    note = (
        db.query(ParentNote)
        .filter(ParentNote.student_id == child.id, ParentNote.status.in_(["approved", "sent"]))
        .order_by(ParentNote.created_at.desc())
        .first()
    )
    latest_note = None
    if note:
        body = note.body_ta if pref_lang == "ta" else note.body_en
        latest_note = ParentHomeNote(
            id=note.id,
            body=body,
            language=pref_lang,
            channel=note.channel,
            created_at=note.created_at,
        )

    # 3. Next booking
    booking = (
        db.query(Booking)
        .filter(Booking.parent_user_id == current_user.id, Booking.status == "confirmed")
        .order_by(Booking.date.asc(), Booking.start_time.asc())
        .first()
    )
    next_booking = None
    if booking:
        teacher = db.query(User).filter(User.id == booking.teacher_id).first()
        t_name = teacher.name if teacher else "Class Teacher"
        next_booking = ParentBookingItem(
            id=booking.id,
            day=booking.date.strftime("%a"),
            date=booking.date.isoformat(),
            time=booking.start_time,
            method=booking.method,
            teacher_name=t_name,
            reminders=booking.reminders or [],
            status=booking.status,
        )

    # 4. Recent checkin
    recent_checkin = None
    last_check = (
        db.query(Checkin)
        .filter(Checkin.parent_user_id == current_user.id)
        .order_by(Checkin.created_at.desc())
        .first()
    )
    if last_check:
        recent_checkin = {
            "id": last_check.id,
            "mood": last_check.mood,
            "has_voice_note": last_check.has_voice_note,
            "voice_note_url": last_check.voice_note_url,
            "created_at": last_check.created_at.isoformat(),
        }

    # 5. Preferences
    shift_w = link.shift_worker if link else False
    prefs = ParentPreferencesResponse(
        preferred_channel=link.preferred_channel if link else "whatsapp",
        preferred_language=pref_lang,
        no_smartphone=link.no_smartphone if link else False,
        shift_worker=shift_w,
        offer_voice_note=shift_w,
    )

    return ParentHomeResponse(
        child=child_summary,
        latest_note=latest_note,
        next_booking=next_booking,
        recent_checkin=recent_checkin,
        preferences=prefs,
    )


@router.post("/checkins", status_code=status.HTTP_201_CREATED)
async def create_parent_checkin(
    mood: Optional[str] = Form(None),
    voice_file: Optional[UploadFile] = File(None),
    checkin_data: Optional[ParentCheckinCreate] = None,
    current_user: User = Depends(require_role("parent")),
    db: Session = Depends(get_db),
):
    """
    Submits parent mood check-in with optional audio voice note.
    Stores voice note file locally behind StorageProvider interface.
    """
    link, child = get_parent_and_child(current_user, db)

    selected_mood = mood or (checkin_data.mood if checkin_data else "great")
    has_voice = False
    voice_url = None

    if voice_file is not None and voice_file.filename:
        content = await voice_file.read()
        storage = get_storage_provider()
        voice_url = storage.save_file(content, voice_file.filename, subfolder="checkins")
        has_voice = True
    elif checkin_data and checkin_data.has_voice_note:
        has_voice = True
        voice_url = checkin_data.voice_note_url or "/uploads/checkins/sample_voice.wav"

    checkin = Checkin(
        parent_user_id=current_user.id,
        student_id=child.id,
        mood=selected_mood,
        has_voice_note=has_voice,
        voice_note_url=voice_url,
    )
    db.add(checkin)
    db.commit()
    db.refresh(checkin)

    return {
        "id": checkin.id,
        "mood": checkin.mood,
        "has_voice_note": checkin.has_voice_note,
        "voice_note_url": checkin.voice_note_url,
        "created_at": checkin.created_at.isoformat(),
        "status": "success",
    }


@router.get("/slots", response_model=ParentSlotsResponse)
def get_parent_slots(
    week: Optional[str] = None,
    current_user: User = Depends(require_role("parent", "teacher")),
    db: Session = Depends(get_db),
):
    """
    PRODUCT RULE 5: Parent call windows stay inside school hours; evening slots only Tue and Thu.
    Returns 5-minute slots respecting school hours and Tue/Thu evening restrictions.
    """
    windows = [
        WindowSlots(
            id=w["id"],
            label=w["label"],
            time=w["time"],
            extended=w["extended"],
            slots=w["slots"],
        )
        for w in WINDOWS_CONFIG
    ]

    # Find teacher bookings to mark occupied slots
    link, child = get_parent_and_child(current_user, db)
    teacher_id = None
    if child and child.class_group and child.class_group.teachers:
        teacher_id = child.class_group.teachers[0].teacher_id
    else:
        teacher_obj = db.query(User).filter(User.role == "teacher", User.school_id == current_user.school_id).first()
        teacher_id = teacher_obj.id if teacher_obj else current_user.id

    # Baseline bookings
    booked_map: Dict[str, str] = {
        "Mon-am": "Meena's mother",
        "Tue-lunch": "Arun's grandmother",
        "Wed-pm": "Vikram's mother",
        "Thu-eve": "Rahul's father",
    }

    # Query active bookings
    active_bookings = (
        db.query(Booking)
        .filter(Booking.teacher_id == teacher_id, Booking.status == "confirmed")
        .all()
    )
    for b in active_bookings:
        day_str = b.date.strftime("%a")
        w_id = b.window_id
        student_name = b.student.name if b.student else "Student"
        relation = b.student.parents[0].relation if b.student and b.student.parents else "Parent"
        booked_map[f"{day_str}-{w_id}"] = f"{student_name}'s {relation}"

    return ParentSlotsResponse(
        days=DAYS_LIST,
        windows=windows,
        booked=booked_map,
    )


@router.post("/bookings", response_model=ParentBookingItem, status_code=status.HTTP_201_CREATED)
def create_parent_booking(
    booking_in: ParentBookingCreate,
    current_user: User = Depends(require_role("parent", "teacher")),
    db: Session = Depends(get_db),
):
    """
    Confirms a 5-minute parent call.
    PRODUCT RULE 5: Parent call windows stay inside school hours; evening slots only Tue and Thu.
    Handles double-booking race condition with HTTP 409 Conflict.
    """
    # 1. Validate call window and day
    validate_booking_window(
        day=booking_in.day,
        window_id=booking_in.window_id or "am",
        slot_time=booking_in.time,
    )

    link, child = get_parent_and_child(current_user, db)
    teacher_id = None
    if child and child.class_group and child.class_group.teachers:
        teacher_id = child.class_group.teachers[0].teacher_id
    else:
        teacher_obj = db.query(User).filter(User.role == "teacher", User.school_id == current_user.school_id).first()
        teacher_id = teacher_obj.id if teacher_obj else current_user.id

    # Compute booking date for target weekday
    target_weekday = DAYS_MAP.get(booking_in.day, 1)
    today = date.today()
    days_ahead = (target_weekday - today.weekday()) % 7
    if days_ahead == 0:
        days_ahead = 7
    booking_date = today + timedelta(days=days_ahead)

    # 2. Check existing confirmed booking for teacher at this slot (Pre-check)
    existing = (
        db.query(Booking)
        .filter(
            Booking.teacher_id == teacher_id,
            Booking.date == booking_date,
            Booking.start_time == booking_in.time,
            Booking.status == "confirmed",
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Slot {booking_in.day} at {booking_in.time} is already booked. Please select another time.",
        )

    teacher_user = db.query(User).filter(User.id == teacher_id).first()
    teacher_name = teacher_user.name if teacher_user else "Class Teacher"

    booking = Booking(
        parent_user_id=current_user.id,
        student_id=child.id,
        teacher_id=teacher_id,
        date=booking_date,
        start_time=booking_in.time,
        duration_min=5,
        method=booking_in.method,
        reminders=booking_in.reminders,
        status="confirmed",
    )

    # 3. Race condition handling on unique constraint (teacher_id, date, start_time)
    try:
        db.add(booking)
        db.commit()
        db.refresh(booking)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Conflict: this slot was just booked by another family. Please choose an alternate slot.",
        )

    return ParentBookingItem(
        id=booking.id,
        day=booking.date.strftime("%a"),
        date=booking.date.isoformat(),
        time=booking.start_time,
        method=booking.method,
        teacher_name=teacher_name,
        reminders=booking.reminders or [],
        status=booking.status,
    )


@router.delete("/bookings/{id}")
def cancel_parent_booking(
    id: str,
    current_user: User = Depends(require_role("parent", "teacher")),
    db: Session = Depends(get_db),
):
    """
    Cancels a parent booking. Parents can only cancel their own bookings.
    """
    booking = db.query(Booking).filter(Booking.id == id).first()
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found.")

    if current_user.role == "parent" and booking.parent_user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only cancel your own bookings.")

    booking.status = "cancelled"
    db.commit()
    return {"status": "cancelled", "id": id}


@router.get("/bookings/{id}.ics")
def download_booking_ics(
    id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Generates a RFC 5545 valid .ics iCalendar file with selected reminders as VALARMs.
    """
    booking = db.query(Booking).filter(Booking.id == id).first()
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found.")

    # Ownership check: Parent can only access their own booking
    if current_user.role == "parent" and booking.parent_user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden: You cannot access another family's calendar event.")

    child_name = booking.student.name if booking.student else "Student"
    teacher_name = booking.student.class_group.teachers[0].teacher.name if (booking.student and booking.student.class_group and booking.student.class_group.teachers) else "Class Teacher"

    # Parse time e.g. "7:30" or "1:00"
    raw_time = booking.start_time
    is_pm = "pm" in raw_time.lower() or int(raw_time.split(":")[0]) in [1, 2, 3, 4, 5, 6]
    parts = raw_time.replace("AM", "").replace("PM", "").strip().split(":")
    hour = int(parts[0])
    minute = int(parts[1]) if len(parts) > 1 else 0
    if is_pm and hour < 12:
        hour += 12

    d_str = booking.date.strftime("%Y%m%d")
    dtstart = f"{d_str}T{hour:02d}{minute:02d}00"
    end_minute = minute + booking.duration_min
    end_hour = hour + (end_minute // 60)
    end_minute = end_minute % 60
    dtend = f"{d_str}T{end_hour:02d}{end_minute:02d}00"

    # Build VALARM components for each reminder
    valarms = []
    reminders = booking.reminders or []
    if "hour" in reminders or "1 hour before" in reminders:
        valarms.append("BEGIN:VALARM\r\nTRIGGER:-PT1H\r\nACTION:DISPLAY\r\nDESCRIPTION:EduPulse call in 1 hour\r\nEND:VALARM")
    if "day" in reminders or "1 day before" in reminders:
        valarms.append("BEGIN:VALARM\r\nTRIGGER:-P1D\r\nACTION:DISPLAY\r\nDESCRIPTION:EduPulse call tomorrow\r\nEND:VALARM")
    if "five" in reminders or "5 min before" in reminders:
        valarms.append("BEGIN:VALARM\r\nTRIGGER:-PT5M\r\nACTION:DISPLAY\r\nDESCRIPTION:EduPulse call in 5 minutes\r\nEND:VALARM")

    valarm_text = "\r\n".join(valarms)
    if valarm_text:
        valarm_text = "\r\n" + valarm_text

    ics_content = (
        "BEGIN:VCALENDAR\r\n"
        "VERSION:2.0\r\n"
        "PRODID:-//EduPulse//Parent Connect//EN\r\n"
        "CALSCALE:GREGORIAN\r\n"
        "METHOD:PUBLISH\r\n"
        "BEGIN:VEVENT\r\n"
        f"UID:{booking.id}@edupulse.demo\r\n"
        f"DTSTAMP:{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}\r\n"
        f"DTSTART:{dtstart}\r\n"
        f"DTEND:{dtend}\r\n"
        f"SUMMARY:5-minute check-in with {child_name}'s teacher ({teacher_name})\r\n"
        f"DESCRIPTION:Short five-minute call about {child_name}'s progress. The teacher will call you.\r\n"
        "STATUS:CONFIRMED"
        f"{valarm_text}\r\n"
        "END:VEVENT\r\n"
        "END:VCALENDAR\r\n"
    )

    return Response(
        content=ics_content,
        media_type="text/calendar",
        headers={"Content-Disposition": f'attachment; filename="edupulse-call-{booking.id}.ics"'},
    )


@router.patch("/preferences", response_model=ParentPreferencesResponse)
def update_parent_preferences(
    pref_in: ParentPreferencesUpdate,
    current_user: User = Depends(require_role("parent")),
    db: Session = Depends(get_db),
):
    """
    Updates parent communication preferences (channel, language, smartphone, shift-worker).
    """
    link, child = get_parent_and_child(current_user, db)
    if not link:
        # Create link if missing
        link = ParentLink(
            parent_user_id=current_user.id,
            student_id=child.id,
            relation="Parent",
            preferred_channel="whatsapp",
            preferred_language="en",
        )
        db.add(link)

    if pref_in.channel is not None:
        link.preferred_channel = pref_in.channel.lower()
    if pref_in.language is not None:
        link.preferred_language = pref_in.language.lower()
        current_user.language = pref_in.language.lower()
    if pref_in.no_smartphone is not None:
        link.no_smartphone = pref_in.no_smartphone
    if pref_in.shift_worker is not None:
        link.shift_worker = pref_in.shift_worker

    db.commit()
    db.refresh(link)

    return ParentPreferencesResponse(
        preferred_channel=link.preferred_channel,
        preferred_language=link.preferred_language,
        no_smartphone=link.no_smartphone,
        shift_worker=link.shift_worker,
        offer_voice_note=link.shift_worker,
    )


# -------------------------------------------------------------------------
# Webhook and Voice Simulation Routes (Mounted under /sms and /voice)
# -------------------------------------------------------------------------

sms_router = APIRouter(prefix="/sms", tags=["SMS Webhooks"])
voice_router = APIRouter(prefix="/voice", tags=["Voice Telephony Simulation"])


@sms_router.post("/inbound")
def handle_sms_inbound(
    payload: InboundSMSRequest,
    db: Session = Depends(get_db),
):
    """
    Inbound SMS webhook: parses reply codes ("1" going well, "2" request call, "3" desk).
    Updates callback_queue when code is "2".
    """
    result = process_inbound_sms(
        db=db,
        sender_phone=payload.from_phone or "",
        body=payload.body,
        student_id=payload.student_id,
        parent_user_id=payload.parent_user_id,
    )
    return result


@voice_router.post("/simulate")
def handle_voice_simulate(
    payload: VoiceSimulateRequest,
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Simulated automated voice call endpoint. Keypad choices POST here and record outcome.
    "1" -> Heard update
    "2" -> Requested callback (enqueues to callback_queue)
    "3" -> Leave voice message
    """
    parent_user_id = payload.parent_user_id or (current_user.id if current_user else None)
    if not parent_user_id:
        parent_user = db.query(User).filter(User.role == "parent").first()
        parent_user_id = parent_user.id if parent_user else "demo-parent-id"

    result = process_voice_simulation(
        db=db,
        parent_user_id=parent_user_id,
        keypad_input=payload.keypad_input,
        student_id=payload.student_id,
    )
    return result
