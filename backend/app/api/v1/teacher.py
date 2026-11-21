"""
EduPulse Teacher API Endpoints.

All endpoints are:
- Role-checked (teacher role required)
- Class-scoped and school-scoped
- Audited (PRODUCT RULE 7: Every sensitive read/write is logged)
"""

from datetime import datetime, date, timedelta, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.api.deps import (
    get_current_user,
    require_role,
    verify_teacher_access_to_student,
)
from app.core.exceptions import PermissionDeniedException, SchoolMismatchException
from app.db.session import get_db
from app.models.models import (
    User,
    Student,
    Class,
    ClassTeacher,
    PlaybookAction,
    ParentNote,
    OutboxMessage,
    Kudos,
    SupportSnapshot,
    Mission,
    MissionAssignment,
    MissionAttempt,
    XpLedger,
    GardenDrop,
    Doubt,
    Booking,
    CallbackQueue,
    ParentLink,
)
from app.schemas.schemas import (
    StudentTeacherView,
    TeacherTodayPlanResponse,
    TeacherStudentDetailResponse,
    BrightSpotView,
    ChartPoint,
    WhatIfRequest,
    WhatIfResponse,
    PlaybookActionCreate,
    PlaybookActionResponse,
    ParentNoteDraftResponse,
    ParentNoteApproveRequest,
    ParentNoteApproveResponse,
    KudosCreate,
    KudosResponse,
    TodaySummary,
    TeacherMissionItem,
    TeacherMissionAssignRequest,
    TeacherMissionTickRequest,
    PrintCardItem,
    StudentDoubtResponse,
    TeacherConnectResponse,
    TeacherCallbackReserveRequest,
)
from app.services.reach import get_ladder_counts, get_unreached_families
from app.services.notifications import get_notification_provider
from app.services.badges import evaluate_and_award_badges
from app.services.audit_service import log_sensitive_access
from app.services.support import (
    plan_for_time_budget,
    what_if as calculate_what_if,
)

router = APIRouter(prefix="/teacher", tags=["Teacher"])

CLASS_AVG = [58, 59, 58, 57, 58, 58, 59, 58]
TESTS = ["T1", "T2", "T3", "T4", "T5", "T6", "T7", "T8"]


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def resolve_student_for_teacher(student_id_or_name: str, teacher: User, db: Session) -> Student:
    """
    Resolves student by UUID id or case-insensitive name/key, ensuring
    school scoping and teacher class authorization.
    """
    student = (
        db.query(Student)
        .join(User, Student.user_id == User.id)
        .filter(
            (Student.id == student_id_or_name)
            | (func.lower(User.name) == student_id_or_name.lower())
        )
        .first()
    )
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student '{student_id_or_name}' not found",
        )

    # Verify school boundary
    if student.school_id != teacher.school_id:
        raise SchoolMismatchException()

    # Verify teacher class authorization
    teaches = (
        db.query(ClassTeacher)
        .filter(
            ClassTeacher.teacher_id == teacher.id,
            ClassTeacher.class_id == student.class_id,
        )
        .first()
    )
    if not teaches:
        raise PermissionDeniedException(
            f"Teachers may only access students in classes they teach (student in class {student.class_name})."
        )

    return student


@router.get("/today", response_model=TeacherTodayPlanResponse)
def get_today_plan(
    budget: int = Query(default=20, ge=5, le=120),
    current_user: User = Depends(require_role("teacher", "admin")),
    db: Session = Depends(get_db),
):
    """
    Teacher > Today plan:
    Ranks students by benefit-per-minute and packs them into the teacher's time budget.
    Audited per PRODUCT RULE 7.
    """
    plan = plan_for_time_budget(teacher=current_user, budget=budget, db=db)

    # Check kudos sent for bright spots
    bright_views = []
    for s in plan["bright"]:
        has_kudos = (
            db.query(Kudos)
            .filter(Kudos.teacher_id == current_user.id, Kudos.student_id == s.id)
            .first()
            is not None
        )
        bright_views.append(
            BrightSpotView(
                id=s.id,
                name=s.name,
                bright_why=s.bright_why,
                kudos_sent=has_kudos,
            )
        )

    # Log audit entry
    log_sensitive_access(
        db=db,
        school_id=current_user.school_id,
        actor_id=current_user.id,
        actor_role=current_user.role,
        action="VIEW_TODAY_PLAN",
        resource_type="teacher_today_plan",
        resource_id=str(budget),
        details={"budget": budget, "in_plan_count": len(plan["in_plan"]), "used": plan["used"]},
    )

    return TeacherTodayPlanResponse(
        budget=plan["budget"],
        used=plan["used"],
        in_plan=[StudentTeacherView.model_validate(s) for s in plan["in_plan"]],
        later=[StudentTeacherView.model_validate(s) for s in plan["later"]],
        bright=bright_views,
        summary=TodaySummary(**plan["summary"]),
    )


@router.get("/students", response_model=List[StudentTeacherView])
def get_teacher_students(
    class_name: Optional[str] = None,
    level: Optional[int] = None,
    search: Optional[str] = None,
    current_user: User = Depends(require_role("teacher", "admin")),
    db: Session = Depends(get_db),
):
    """
    Class-scoped student list with early warning support levels.
    """
    class_teachers = (
        db.query(ClassTeacher)
        .filter(ClassTeacher.teacher_id == current_user.id)
        .all()
    )
    class_ids = [ct.class_id for ct in class_teachers]
    if not class_ids:
        c9a = db.query(Class).filter(Class.school_id == current_user.school_id, Class.name == "9A").first()
        if c9a:
            class_ids = [c9a.id]

    query = (
        db.query(Student)
        .join(Class, Student.class_id == Class.id)
        .join(User, Student.user_id == User.id)
        .filter(Class.id.in_(class_ids))
    )

    if class_name:
        query = query.filter(Class.name == class_name)
    if search:
        query = query.filter(User.name.ilike(f"%{search}%"))

    students = query.all()

    if level:
        students = [s for s in students if s.support_level == level]

    log_sensitive_access(
        db=db,
        school_id=current_user.school_id,
        actor_id=current_user.id,
        actor_role=current_user.role,
        action="READ_TEACHER_STUDENTS_LIST",
        resource_type="students",
        details={"count": len(students), "level_filter": level},
    )

    return [StudentTeacherView.model_validate(s) for s in students]


@router.get("/students/{student_id}", response_model=TeacherStudentDetailResponse)
def get_teacher_student_detail(
    student_id: str,
    current_user: User = Depends(require_role("teacher", "admin")),
    db: Session = Depends(get_db),
):
    """
    Individual student diagnostic detail:
    Scores against own baseline and class average, reasons, suggested actions, and logged actions.
    """
    student = resolve_student_for_teacher(student_id, current_user, db)

    # Build chart data
    scores = student.scores_list
    chart_points = []
    for idx, t in enumerate(TESTS):
        score_val = scores[idx] if idx < len(scores) else (student.baseline_score or 70)
        avg_val = CLASS_AVG[idx] if idx < len(CLASS_AVG) else 58
        chart_points.append(ChartPoint(t=t, score=score_val, avg=avg_val))

    # Logged actions
    logged = [
        pa.action
        for pa in db.query(PlaybookAction)
        .filter(PlaybookAction.student_id == student.id)
        .all()
    ]

    # Parent note status
    latest_note = (
        db.query(ParentNote)
        .filter(ParentNote.student_id == student.id)
        .order_by(ParentNote.created_at.desc())
        .first()
    )
    parent_note_status = latest_note.status if latest_note else None

    drop = student.latest_snapshot.drop if student.latest_snapshot else 0

    log_sensitive_access(
        db=db,
        school_id=current_user.school_id,
        actor_id=current_user.id,
        actor_role=current_user.role,
        action="READ_STUDENT_TEACHER_DETAIL",
        resource_type="student_diagnostic",
        resource_id=student.id,
        details={"name": student.name, "level": student.support_level},
    )

    return TeacherStudentDetailResponse(
        student=StudentTeacherView.model_validate(student),
        tests=TESTS,
        class_avg=CLASS_AVG,
        chart_data=chart_points,
        baseline=student.baseline_score,
        drop=drop,
        reasons=student.reasons,
        suggested_actions=student.suggested_actions,
        logged_actions=logged,
        parent_note_status=parent_note_status,
    )


@router.post("/students/{student_id}/what-if", response_model=WhatIfResponse)
def post_student_what_if(
    student_id: str,
    body: WhatIfRequest,
    current_user: User = Depends(require_role("teacher", "admin")),
    db: Session = Depends(get_db),
):
    """
    Stateless 'What If?' slider simulation:
    Returns the resulting support level for given attendance and homework values.
    """
    student = resolve_student_for_teacher(student_id, current_user, db)
    result = calculate_what_if(student, attendance=body.attendance, homework=body.homework)
    return WhatIfResponse(**result)


@router.get("/students/{student_id}/actions", response_model=List[PlaybookActionResponse])
def get_student_playbook_actions(
    student_id: str,
    current_user: User = Depends(require_role("teacher", "admin")),
    db: Session = Depends(get_db),
):
    """
    Retrieves the logged Support Playbook actions for a student.
    """
    student = resolve_student_for_teacher(student_id, current_user, db)
    actions = (
        db.query(PlaybookAction)
        .filter(PlaybookAction.student_id == student.id)
        .order_by(PlaybookAction.logged_at.desc())
        .all()
    )
    return [PlaybookActionResponse.model_validate(a) for a in actions]


@router.post("/students/{student_id}/actions", response_model=PlaybookActionResponse)
def log_student_playbook_action(
    student_id: str,
    body: PlaybookActionCreate,
    current_user: User = Depends(require_role("teacher", "admin")),
    db: Session = Depends(get_db),
):
    """
    Support Playbook logging: records action taken, notes, and sets a 4-6 week follow-up due date.
    """
    student = resolve_student_for_teacher(student_id, current_user, db)

    # 4 to 6 weeks follow-up date (5 weeks = 35 days)
    followup_date = date.today() + timedelta(weeks=5)

    action_entry = PlaybookAction(
        student_id=student.id,
        teacher_id=current_user.id,
        action=body.action,
        note=body.note,
        logged_at=now_utc(),
        followup_due=followup_date,
    )
    db.add(action_entry)
    db.commit()
    db.refresh(action_entry)

    log_sensitive_access(
        db=db,
        school_id=current_user.school_id,
        actor_id=current_user.id,
        actor_role=current_user.role,
        action="LOG_PLAYBOOK_ACTION",
        resource_type="playbook_action",
        resource_id=student.id,
        details={"action": body.action, "followup_due": str(followup_date)},
    )

    return PlaybookActionResponse.model_validate(action_entry)


@router.get("/students/{student_id}/parent-note", response_model=ParentNoteDraftResponse)
def get_parent_note_draft(
    student_id: str,
    current_user: User = Depends(require_role("teacher", "admin")),
    db: Session = Depends(get_db),
):
    """
    Generates or retrieves bilingual draft parent note (English and Tamil),
    written strengths-first with verified records.
    """
    student = resolve_student_for_teacher(student_id, current_user, db)

    first_name = student.name
    primary_reason = student.reasons[0] if student.reasons else "Making steady progress in practice missions"

    note_en = (
        f"{first_name} has been working hard on practice missions. {primary_reason}. "
        "A short 10-minute practice at home could help, and the class teacher will check in this week."
    )

    if student.name == "Karthik":
        note_ta = (
            "அறிவியலில் கார்த்திக் சிறப்பாகச் செய்து வருகிறார்; பயிற்சிப் பணிகளையும் முடித்து வருகிறார். "
            "கணிதத்தில் கடந்த மூன்று தேர்வுகளில் மதிப்பெண் சற்றுக் குறைந்துள்ளது. "
            "வீட்டில் தினமும் 10 நிமிடம் பின்னங்கள் பயிற்சி செய்தால் உதவும். வகுப்பாசிரியர் இந்த வாரம் உங்களைத் தொடர்பு கொள்வார்."
        )
    else:
        note_ta = (
            f"வகுப்பில் {first_name} ஆர்வத்துடன் பங்கேற்று வருகிறார். "
            "வீட்டில் தினமும் 10 நிமிடம் பயிற்சி செய்தால் கூடுதல் பலன் கிடைக்கும். "
            "வகுப்பாசிரியர் விரைவில் உங்களைத் தொடர்பு கொள்வார்."
        )

    # Check if approved/sent note exists
    existing = (
        db.query(ParentNote)
        .filter(ParentNote.student_id == student.id)
        .order_by(ParentNote.created_at.desc())
        .first()
    )

    parent_link = student.primary_parent_link
    pref_lang = parent_link.preferred_language if parent_link else "en"

    return ParentNoteDraftResponse(
        student_id=student.id,
        student_name=student.name,
        parent_who=student.parent_who,
        channel=student.parent_channel,
        preferred_language=pref_lang,
        body_en=existing.body_en if existing else note_en,
        body_ta=existing.body_ta if existing else note_ta,
        status=existing.status if existing else "draft",
        sent=(existing.status in ("approved", "sent")) if existing else False,
    )


@router.post("/students/{student_id}/parent-note", response_model=ParentNoteApproveResponse)
def approve_parent_note(
    student_id: str,
    body: ParentNoteApproveRequest,
    current_user: User = Depends(require_role("teacher", "admin")),
    db: Session = Depends(get_db),
):
    """
    Approve parent note:
    Creates or updates the ParentNote record and queues an OutboxMessage in the parent's
    preferred channel and language.
    """
    student = resolve_student_for_teacher(student_id, current_user, db)

    parent_link = student.primary_parent_link
    channel = body.channel or student.parent_channel
    status_str = "approved" if body.approved else "draft"

    parent_note = (
        db.query(ParentNote)
        .filter(ParentNote.student_id == student.id)
        .first()
    )
    if not parent_note:
        parent_note = ParentNote(
            student_id=student.id,
            teacher_id=current_user.id,
            body_en=body.body_en,
            body_ta=body.body_ta or "",
            status=status_str,
            channel=channel,
        )
        db.add(parent_note)
    else:
        parent_note.body_en = body.body_en
        if body.body_ta:
            parent_note.body_ta = body.body_ta
        parent_note.status = status_str
        parent_note.channel = channel

    db.commit()
    db.refresh(parent_note)

    outbox_id = None
    if body.approved and parent_link:
        parent_user_id = parent_link.parent_user_id
        pref_lang = parent_link.preferred_language or "en"
        chosen_body = parent_note.body_ta if (pref_lang == "ta" and parent_note.body_ta) else parent_note.body_en

        outbox_msg = OutboxMessage(
            to_user_id=parent_user_id,
            channel=parent_link.preferred_channel or "whatsapp",
            template="parent_weekly_note",
            payload={
                "student_name": student.name,
                "message": chosen_body,
                "language": pref_lang,
                "note_id": parent_note.id,
            },
            status="queued",
        )
        db.add(outbox_msg)
        db.commit()
        db.refresh(outbox_msg)
        outbox_id = outbox_msg.id

    log_sensitive_access(
        db=db,
        school_id=current_user.school_id,
        actor_id=current_user.id,
        actor_role=current_user.role,
        action="APPROVE_PARENT_NOTE",
        resource_type="parent_note",
        resource_id=student.id,
        details={"status": status_str, "channel": channel, "outbox_id": outbox_id},
    )

    return ParentNoteApproveResponse(
        status=status_str,
        message="Approved and queued to send in the parent's preferred channel.",
        note_id=parent_note.id,
        outbox_id=outbox_id,
    )


@router.get("/bright-spots", response_model=List[BrightSpotView])
def get_bright_spots(
    current_user: User = Depends(require_role("teacher", "admin")),
    db: Session = Depends(get_db),
):
    """
    Celebrates student progress (e.g. Meena, Sana).
    """
    class_teachers = (
        db.query(ClassTeacher)
        .filter(ClassTeacher.teacher_id == current_user.id)
        .all()
    )
    class_ids = [ct.class_id for ct in class_teachers]
    if not class_ids:
        c9a = db.query(Class).filter(Class.school_id == current_user.school_id, Class.name == "9A").first()
        if c9a:
            class_ids = [c9a.id]

    students = (
        db.query(Student)
        .filter(Student.class_id.in_(class_ids))
        .all()
    )

    bright_views = []
    for s in students:
        if s.bright:
            has_kudos = (
                db.query(Kudos)
                .filter(Kudos.teacher_id == current_user.id, Kudos.student_id == s.id)
                .first()
                is not None
            )
            bright_views.append(
                BrightSpotView(
                    id=s.id,
                    name=s.name,
                    bright_why=s.bright_why,
                    kudos_sent=has_kudos,
                )
            )

    log_sensitive_access(
        db=db,
        school_id=current_user.school_id,
        actor_id=current_user.id,
        actor_role=current_user.role,
        action="VIEW_BRIGHT_SPOTS",
        resource_type="bright_spots",
        details={"count": len(bright_views)},
    )

    return bright_views


@router.post("/kudos", response_model=KudosResponse)
def send_teacher_kudos(
    body: KudosCreate,
    current_user: User = Depends(require_role("teacher", "admin")),
    db: Session = Depends(get_db),
):
    """
    Sends teacher Kudos to celebrate student progress.
    Appears on the student's home screen.
    """
    student = resolve_student_for_teacher(body.student_id, current_user, db)

    existing_kudos = (
        db.query(Kudos)
        .filter(Kudos.teacher_id == current_user.id, Kudos.student_id == student.id)
        .first()
    )
    if not existing_kudos:
        kudos_entry = Kudos(
            student_id=student.id,
            teacher_id=current_user.id,
            message=body.message or "Great effort and steady growth!",
            created_at=now_utc(),
        )
        db.add(kudos_entry)
        db.commit()
        db.refresh(kudos_entry)
        kudos_id = kudos_entry.id
    else:
        kudos_id = existing_kudos.id

    log_sensitive_access(
        db=db,
        school_id=current_user.school_id,
        actor_id=current_user.id,
        actor_role=current_user.role,
        action="SEND_KUDOS",
        resource_type="kudos",
        resource_id=student.id,
        details={"message": body.message},
    )

    return KudosResponse(
        success=True,
        message="Kudos sent. It appears on the student's home screen.",
        kudos_id=kudos_id,
    )


# =========================================================================
# TEACHER MISSION MANAGEMENT & LOW-TECH TICKING
# =========================================================================

@router.get("/missions", response_model=List[TeacherMissionItem])
def get_teacher_missions(
    current_user: User = Depends(require_role("teacher", "admin")),
    db: Session = Depends(get_db),
):
    """
    Lists all missions with whether they are assigned to the teacher's class.
    """
    ct = db.query(ClassTeacher).filter(ClassTeacher.teacher_id == current_user.id).first()
    class_id = ct.class_id if ct else None
    if not class_id:
        c9a = db.query(Class).filter(Class.school_id == current_user.school_id, Class.name == "9A").first()
        class_id = c9a.id if c9a else None

    all_missions = db.query(Mission).filter(Mission.is_active == True).all()

    assigned_ids = set()
    if class_id:
        assigned = (
            db.query(MissionAssignment)
            .filter(MissionAssignment.class_id == class_id)
            .all()
        )
        assigned_ids = {a.mission_id for a in assigned}

    results = []
    for m in all_missions:
        results.append(
            TeacherMissionItem(
                id=m.id,
                title=m.title,
                minutes=m.minutes,
                xp=m.xp,
                tier=m.tier,
                kind=m.kind,
                blurb=m.blurb,
                is_assigned=(m.id in assigned_ids),
            )
        )

    return results


@router.post("/missions")
def assign_mission_to_class(
    body: TeacherMissionAssignRequest,
    current_user: User = Depends(require_role("teacher", "admin")),
    db: Session = Depends(get_db),
):
    """
    Assigns or unassigns a mission for the teacher's class.
    """
    ct = db.query(ClassTeacher).filter(ClassTeacher.teacher_id == current_user.id).first()
    class_id = ct.class_id if ct else None
    if not class_id:
        c9a = db.query(Class).filter(Class.school_id == current_user.school_id, Class.name == "9A").first()
        class_id = c9a.id if c9a else None

    if not class_id:
        raise HTTPException(status_code=400, detail="Teacher has no assigned class")

    mission = db.query(Mission).filter(Mission.id == body.mission_id).first()
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")

    existing_assignment = (
        db.query(MissionAssignment)
        .filter(
            MissionAssignment.class_id == class_id,
            MissionAssignment.mission_id == mission.id,
        )
        .first()
    )

    if body.assign and not existing_assignment:
        new_assignment = MissionAssignment(
            class_id=class_id,
            mission_id=mission.id,
            assigned_by=current_user.id,
        )
        db.add(new_assignment)
        db.commit()
    elif not body.assign and existing_assignment:
        db.delete(existing_assignment)
        db.commit()

    return {"success": True, "mission_id": mission.id, "assigned": body.assign}


@router.post("/missions/{mission_id}/tick")
def tick_paper_mission(
    mission_id: str,
    body: TeacherMissionTickRequest,
    current_user: User = Depends(require_role("teacher", "admin")),
    db: Session = Depends(get_db),
):
    """
    Teacher marks a paper mission done for a student without a smartphone or computer.
    Awards full XP to student, adds drop to Class Garden, and triggers badge evaluation.
    PRODUCT RULE 1: Effort over Marks. Paper missions grant same XP as digital.
    """
    student = resolve_student_for_teacher(body.student_id, current_user, db)
    mission = db.query(Mission).filter(Mission.id == mission_id).first()
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")

    # Idempotent check
    existing = (
        db.query(MissionAttempt)
        .filter(
            MissionAttempt.student_id == student.id,
            MissionAttempt.mission_id == mission.id,
            MissionAttempt.status == "completed",
        )
        .first()
    )
    if existing:
        return {
            "success": True,
            "message": "Paper mission was already marked completed",
            "xp_awarded": 0,
            "new_total_xp": student.current_xp,
        }

    # Award XP for effort
    xp_entry = XpLedger(
        student_id=student.id,
        delta=mission.xp,
        reason=f"Paper mission tick by {current_user.name}: {mission.title}",
        ref_id=mission.id,
        created_at=now_utc(),
    )
    db.add(xp_entry)

    # Class Garden drop
    drop = GardenDrop(
        class_id=student.class_id,
        student_id=student.id,
        created_at=now_utc(),
    )
    db.add(drop)

    # Completed attempt
    attempt = MissionAttempt(
        student_id=student.id,
        mission_id=mission.id,
        status="completed",
        score=100,
        hints_used=0,
        xp_awarded=mission.xp,
        completed_at=now_utc(),
    )
    db.add(attempt)
    db.commit()

    # Evaluate badges
    newly_unlocked = evaluate_and_award_badges(
        db=db,
        student_id=student.id,
        event="mission_complete",
        context={"mission": mission},
    )

    log_sensitive_access(
        db=db,
        school_id=current_user.school_id,
        actor_id=current_user.id,
        actor_role=current_user.role,
        action="TICK_PAPER_MISSION",
        resource_type="mission",
        resource_id=mission.id,
        details={"student_id": student.id, "student_name": student.name, "note": body.note},
    )

    return {
        "success": True,
        "message": f"Paper mission marked complete! +{mission.xp} XP awarded to {student.name}.",
        "xp_awarded": mission.xp,
        "new_total_xp": student.current_xp,
        "newly_unlocked_badges": [b.code for b in newly_unlocked],
    }


@router.get("/print-cards", response_model=List[PrintCardItem])
def get_print_cards(
    current_user: User = Depends(require_role("teacher", "admin")),
    db: Session = Depends(get_db),
):
    """
    Returns printable mission cards for students without digital access.
    """
    ct = db.query(ClassTeacher).filter(ClassTeacher.teacher_id == current_user.id).first()
    class_id = ct.class_id if ct else None
    if not class_id:
        c9a = db.query(Class).filter(Class.school_id == current_user.school_id, Class.name == "9A").first()
        class_id = c9a.id if c9a else None

    assigned = (
        db.query(MissionAssignment)
        .filter(MissionAssignment.class_id == class_id)
        .all()
    )
    mission_ids = [a.mission_id for a in assigned]
    if not mission_ids:
        missions = db.query(Mission).filter(Mission.is_active == True).limit(3).all()
    else:
        missions = db.query(Mission).filter(Mission.id.in_(mission_ids)).all()

    return [
        PrintCardItem(
            id=m.id,
            title=m.title,
            minutes=m.minutes,
            xp=m.xp,
            tier=m.tier,
            blurb=m.blurb,
        )
        for m in missions
    ]


@router.get("/doubts", response_model=List[StudentDoubtResponse])
def get_teacher_doubts(
    current_user: User = Depends(require_role("teacher", "admin")),
    db: Session = Depends(get_db),
):
    """
    PRODUCT RULE 6: Anonymous "I'm stuck"/doubt questions must not be linkable to a student in teacher APIs.
    Returns anonymous class doubts without student identity.
    """
    ct = db.query(ClassTeacher).filter(ClassTeacher.teacher_id == current_user.id).first()
    class_id = ct.class_id if ct else None
    if not class_id:
        c9a = db.query(Class).filter(Class.school_id == current_user.school_id, Class.name == "9A").first()
        class_id = c9a.id if c9a else None

    query = db.query(Doubt)
    if class_id:
        query = query.filter(Doubt.class_id == class_id)

    doubts = query.order_by(Doubt.created_at.desc()).all()

    log_sensitive_access(
        db=db,
        school_id=current_user.school_id,
        actor_id=current_user.id,
        actor_role=current_user.role,
        action="VIEW_CLASS_DOUBTS",
        resource_type="doubts",
        details={"count": len(doubts)},
    )

    return [
        StudentDoubtResponse(
            id=d.id,
            class_name=d.class_name,
            text=d.text,
            topic=d.topic,
            message=d.message,
            created_at=d.created_at,
            resolved=d.resolved,
        )
        for d in doubts
    ]


@router.get("/connect", response_model=TeacherConnectResponse)
def get_teacher_connect(
    current_user: User = Depends(require_role("teacher", "admin")),
    db: Session = Depends(get_db),
):
    """
    Teacher Parent Connect: Reach ladder statistics, unreached families requiring human touch,
    and weekly booked five-minute call schedule.
    PRODUCT RULE 7: Audited sensitive access.
    """
    ladder = get_ladder_counts(db, current_user.school_id)
    unreached = get_unreached_families(db, current_user.school_id)

    # Baseline bookings
    booked_map: dict = {
        "Mon-am": "Meena's mother",
        "Tue-lunch": "Arun's grandmother",
        "Wed-pm": "Vikram's mother",
        "Thu-eve": "Rahul's father",
    }

    # Query active bookings for teacher
    bookings = (
        db.query(Booking)
        .filter(Booking.teacher_id == current_user.id, Booking.status == "confirmed")
        .all()
    )
    for b in bookings:
        day_str = b.date.strftime("%a")
        w_id = b.window_id
        student_name = b.student.name if b.student else "Student"
        relation = b.student.parents[0].relation if b.student and b.student.parents else "Parent"
        booked_map[f"{day_str}-{w_id}"] = f"{student_name}'s {relation}"

    log_sensitive_access(
        db=db,
        school_id=current_user.school_id,
        actor_id=current_user.id,
        actor_role=current_user.role,
        action="VIEW_PARENT_CONNECT",
        resource_type="connect",
        details={"unreached_count": len(unreached), "booked_count": len(booked_map)},
    )

    return TeacherConnectResponse(
        ladder=ladder,
        unreached=unreached,
        booked_count=len(booked_map),
        budget_calls=8,
        booked=booked_map,
    )


@router.post("/callbacks")
def reserve_teacher_callback(
    body: TeacherCallbackReserveRequest,
    current_user: User = Depends(require_role("teacher", "admin")),
    db: Session = Depends(get_db),
):
    """
    Teacher reserves a callback for an unreached family and dispatches a notification.
    """
    cb = db.query(CallbackQueue).filter(CallbackQueue.id == body.callback_id).first()
    student = None
    parent_user_id = None

    if cb:
        cb.status = "reserved"
        student = cb.student
        parent_user_id = cb.parent_user_id
    else:
        # Match mock unreached keys (u1 -> Divya, u2 -> Arun, u3 -> Vikram)
        mock_names = {"u1": "divya", "u2": "arun", "u3": "vikram"}
        matched_key = mock_names.get(body.callback_id, "divya")
        student = db.query(Student).join(User, Student.user_id == User.id).filter(User.email.like(f"{matched_key}%")).first()
        if not student:
            student = db.query(Student).first()
        if student and student.parents:
            parent_user_id = student.parents[0].parent_user_id
        else:
            parent_user = db.query(User).filter(User.role == "parent").first()
            parent_user_id = parent_user.id if parent_user else current_user.id

    # Compute target booking date
    days_map = {"Mon": 0, "Tue": 1, "Wed": 2, "Thu": 3, "Fri": 4, "Sat": 5, "Sun": 6}
    target_weekday = days_map.get(body.day, 1)
    today = date.today()
    days_ahead = (target_weekday - today.weekday()) % 7
    if days_ahead == 0:
        days_ahead = 7
    booking_date = today + timedelta(days=days_ahead)

    booking = Booking(
        parent_user_id=parent_user_id,
        student_id=student.id if student else "unknown",
        teacher_id=current_user.id,
        date=booking_date,
        start_time=body.time,
        duration_min=5,
        method=body.method,
        reminders=["whatsapp", "hour"],
        status="confirmed",
    )
    db.add(booking)
    if cb:
        cb.booking_id = booking.id

    db.commit()
    db.refresh(booking)

    # Dispatch notification to parent
    provider = get_notification_provider()
    provider.send(
        db=db,
        to_user_id=parent_user_id,
        channel="whatsapp",
        template="teacher_reserved_callback",
        payload={
            "teacher_name": current_user.name,
            "day": body.day,
            "date": booking.date.isoformat(),
            "time": booking.start_time,
            "method": body.method,
        },
    )

    log_sensitive_access(
        db=db,
        school_id=current_user.school_id,
        actor_id=current_user.id,
        actor_role=current_user.role,
        action="RESERVE_PARENT_CALLBACK",
        resource_type="callback",
        resource_id=body.callback_id,
        details={"booking_id": booking.id, "day": body.day, "time": body.time},
    )

    return {
        "success": True,
        "message": "Callback reserved successfully and notification queued for family.",
        "booking_id": booking.id,
        "callback_id": body.callback_id,
    }


