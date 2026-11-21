from typing import List
from datetime import date, timedelta
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.api.deps import get_current_user, require_role
from app.db.session import get_db
from app.models.models import User, Student, Class, ParentLink, Booking
from app.schemas.schemas import CallBookingCreate, CallBookingResponse
from app.services.booking_service import validate_booking_window

router = APIRouter(prefix="/bookings", tags=["Parent Call Bookings"])


@router.post("", response_model=CallBookingResponse, status_code=status.HTTP_201_CREATED)
def book_call(
    booking_in: CallBookingCreate,
    current_user: User = Depends(require_role("parent", "teacher")),
    db: Session = Depends(get_db),
):
    """
    PRODUCT RULE 5: Parent call windows stay inside school hours; evening slots only Tue and Thu.
    """
    validate_booking_window(
        day=booking_in.day,
        window_id=booking_in.window_id,
        slot_time=booking_in.slot_time,
    )

    student = None
    teacher_id = None
    if current_user.role == "parent":
        link = db.query(ParentLink).filter(ParentLink.parent_user_id == current_user.id).first()
        if link:
            student = link.student
    else:
        teacher_id = current_user.id
        student = db.query(Student).first()

    if not student:
        student = db.query(Student).first()

    if not teacher_id:
        if student and student.class_group and student.class_group.teachers:
            teacher_id = student.class_group.teachers[0].teacher_id
        else:
            teacher_user = (
                db.query(User)
                .filter(User.role == "teacher", User.school_id == current_user.school_id)
                .first()
            )
            teacher_id = teacher_user.id if teacher_user else current_user.id

    days_map = {"Mon": 0, "Tue": 1, "Wed": 2, "Thu": 3, "Fri": 4, "Sat": 5, "Sun": 6}
    target_weekday = days_map.get(booking_in.day, 1)
    today = date.today()
    days_ahead = (target_weekday - today.weekday()) % 7
    if days_ahead == 0:
        days_ahead = 7
    booking_date = today + timedelta(days=days_ahead)

    booking = Booking(
        parent_user_id=current_user.id if current_user.role == "parent" else (student.parents[0].parent_user_id if student and student.parents else current_user.id),
        student_id=student.id if student else "unknown",
        teacher_id=teacher_id,
        date=booking_date,
        start_time=booking_in.slot_time,
        duration_min=5,
        method=booking_in.method,
        reminders=booking_in.reminders,
        status="confirmed",
    )
    db.add(booking)
    db.commit()
    db.refresh(booking)

    return CallBookingResponse(
        id=booking.id,
        parent_id=booking.parent_user_id,
        day=booking_in.day,
        slot_time=booking.start_time,
        window_id=booking_in.window_id,
        method=booking.method,
        reminders=booking.reminders or [],
        created_at=booking.created_at,
    )


@router.get("", response_model=List[CallBookingResponse])
def list_bookings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = (
        db.query(Booking)
        .join(Student, Booking.student_id == Student.id)
        .join(Class, Student.class_id == Class.id)
        .filter(Class.school_id == current_user.school_id)
    )
    if current_user.role == "parent":
        query = query.filter(Booking.parent_user_id == current_user.id)
    elif current_user.role == "teacher":
        query = query.filter(Booking.teacher_id == current_user.id)

    bookings = query.all()
    results = []
    for b in bookings:
        hour = int(b.start_time.split(":")[0]) if ":" in b.start_time else 9
        w_id = "eve" if hour >= 18 else "pm" if hour >= 14 else "lunch" if hour >= 12 else "am"
        results.append(
            CallBookingResponse(
                id=b.id,
                parent_id=b.parent_user_id,
                day=b.date.strftime("%a"),
                slot_time=b.start_time,
                window_id=w_id,
                method=b.method,
                reminders=b.reminders or [],
                created_at=b.created_at,
            )
        )
    return results
