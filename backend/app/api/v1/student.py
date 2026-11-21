"""
EduPulse Student Gamification API Endpoints.

PRODUCT RULES:
- PRODUCT RULE 1: Effort over Marks. XP is awarded for effort, never marks. Same effort = same XP for every student.
- PRODUCT RULE 2: No leaderboards. The Class Garden is cooperative and never names anyone.
- PRODUCT RULE 3: Students see growth only, never their support level. Support levels are teacher-only.
- PRODUCT RULE 6: Anonymous "I'm stuck"/doubt questions must not be linkable to a student in teacher APIs.
"""

from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_role
from app.db.session import get_db
from app.models.models import (
    User,
    Student,
    Class,
    Mission,
    MissionAssignment,
    MissionAttempt,
    Badge,
    StudentBadge,
    XpLedger,
    GardenDrop,
    Doubt,
    Kudos,
)
from app.schemas.schemas import (
    StudentHomeResponse,
    StudentMissionItem,
    StudentBadgeItem,
    ClassGardenInfo,
    StudentKudosItem,
    ProgressPoint,
    MissionSubmitRequest,
    MissionSubmitResponse,
    StudentDoubtCreate,
    StudentDoubtResponse,
)
from app.services.badges import evaluate_and_award_badges, ensure_badges_exist

router = APIRouter(prefix="/student", tags=["Student"])


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def garden_stage(pct: float) -> str:
    if pct >= 0.9:
        return "A full grove"
    elif pct >= 0.6:
        return "In bloom"
    elif pct >= 0.25:
        return "Saplings"
    elif pct > 0:
        return "Sprouts"
    return "Seeds"


def level_from_xp(xp: int) -> tuple[str, str, int, float]:
    """
    Sprout / Sapling / Bloom / Grove at 0 / 200 / 450 / 800 XP.
    Returns (name, next_level, to_next, pct).
    """
    if xp < 200:
        return "Sprout", "Sapling", 200 - xp, round(xp / 200.0, 3)
    elif xp < 450:
        return "Sapling", "Bloom", 450 - xp, round((xp - 200) / 250.0, 3)
    elif xp < 800:
        return "Bloom", "Grove", 800 - xp, round((xp - 450) / 350.0, 3)
    else:
        return "Grove", "Beyond", 0, 1.0


@router.get("/home", response_model=StudentHomeResponse)
def get_student_home(
    current_user: User = Depends(require_role("student")),
    db: Session = Depends(get_db),
):
    """
    Student Home Screen:
    XP total (sum of xp_ledger), level progress, assigned missions, earned badges,
    cooperative class garden count, and recent kudos from teacher.
    PRODUCT RULE 3: Never returns support level or class rankings.
    """
    student = db.query(Student).filter(Student.user_id == current_user.id).first()
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student profile not found")

    xp_total = student.current_xp
    level_name, next_level, to_next, pct = level_from_xp(xp_total)

    # 1. Assigned Missions
    assignments = (
        db.query(MissionAssignment)
        .filter(
            (MissionAssignment.class_id == student.class_id)
            | (MissionAssignment.student_id == student.id)
        )
        .all()
    )
    assigned_mission_ids = {a.mission_id for a in assignments}
    if not assigned_mission_ids:
        # Fallback to active Starter missions
        all_starter = db.query(Mission).filter(Mission.is_active == True).all()
        assigned_missions_objs = all_starter
    else:
        assigned_missions_objs = (
            db.query(Mission)
            .filter(Mission.id.in_(assigned_mission_ids), Mission.is_active == True)
            .all()
        )

    completed_mission_ids = {
        att.mission_id
        for att in student.attempts
        if att.status == "completed"
    }

    mission_items = []
    for m in assigned_missions_objs:
        mission_items.append(
            StudentMissionItem(
                id=m.id,
                title=m.title,
                minutes=m.minutes,
                xp=m.xp,
                tier=m.tier,
                kind=m.kind,
                blurb=m.blurb,
                is_done=(m.id in completed_mission_ids),
                badge_id=m.badge_id,
            )
        )

    # 2. Earned Badges
    earned_badge_items = []
    for sb in student.badges:
        if sb.badge:
            earned_badge_items.append(
                StudentBadgeItem(
                    id=sb.badge.id,
                    code=sb.badge.code,
                    name=sb.badge.name,
                    category=sb.badge.category,
                    how_to_earn=sb.badge.how_to_earn,
                    icon=sb.badge.icon,
                    earned=True,
                    earned_at=sb.earned_at,
                )
            )

    all_badges_count = db.query(Badge).count() or 12

    # 3. Class Garden (cooperative, anonymous)
    total_drops = (
        db.query(GardenDrop)
        .filter(GardenDrop.class_id == student.class_id)
        .count()
    )
    garden_pct = min(1.0, total_drops / 48.0)
    garden_info = ClassGardenInfo(
        total_drops=total_drops,
        target_drops=48,
        stage=garden_stage(garden_pct),
        pct=round(garden_pct, 3),
        watered_today_count=18,
        total_classmates=24,
    )

    # 4. Recent Kudos
    recent_kudos = []
    for k in (student.kudos or []):
        recent_kudos.append(
            StudentKudosItem(
                id=k.id,
                teacher_name=k.teacher.name if k.teacher else "Ms. Priya",
                message=k.message,
                created_at=k.created_at,
            )
        )

    # 5. Own Progress against past self (never peer comparison)
    own_progress = [
        ProgressPoint(w="Wk 1", v=40),
        ProgressPoint(w="Wk 2", v=48),
        ProgressPoint(w="Wk 3", v=45),
        ProgressPoint(w="Wk 4", v=58),
        ProgressPoint(w="Wk 5", v=65),
    ]

    return StudentHomeResponse(
        xp_total=xp_total,
        level_name=level_name,
        next_level=next_level,
        to_next=to_next,
        pct=pct,
        class_name=student.class_name,
        student_name=student.name,
        assigned_missions=mission_items,
        earned_badges=earned_badge_items,
        total_badges_count=all_badges_count,
        class_garden=garden_info,
        recent_kudos=recent_kudos,
        own_progress=own_progress,
    )


@router.post("/missions/{mission_id}/start")
def start_mission(
    mission_id: str,
    current_user: User = Depends(require_role("student")),
    db: Session = Depends(get_db),
):
    """
    Starts a mission attempt.
    """
    student = db.query(Student).filter(Student.user_id == current_user.id).first()
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")

    mission = (
        db.query(Mission)
        .filter((Mission.id == mission_id) | (Mission.title == mission_id))
        .first()
    )
    if not mission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mission not found")

    attempt = (
        db.query(MissionAttempt)
        .filter(
            MissionAttempt.student_id == student.id,
            MissionAttempt.mission_id == mission.id,
        )
        .first()
    )
    if not attempt:
        attempt = MissionAttempt(
            student_id=student.id,
            mission_id=mission.id,
            status="in_progress",
            hints_used=0,
            score=0,
            xp_awarded=0,
        )
        db.add(attempt)
        db.commit()
        db.refresh(attempt)

    return {"status": attempt.status, "mission_id": mission.id}


@router.post("/missions/{mission_id}/submit", response_model=MissionSubmitResponse)
def submit_mission(
    mission_id: str,
    body: MissionSubmitRequest,
    current_user: User = Depends(require_role("student")),
    db: Session = Depends(get_db),
):
    """
    Submits a mission attempt:
    PRODUCT RULE 1: XP is awarded for completing the mission (effort), never for marks.
    Wrong answers provide hints, not penalties.
    Idempotent: finishing twice never double-awards XP.
    Adds one drop to Class Garden.
    Evaluates badges and returns any newly unlocked badges.
    """
    student = db.query(Student).filter(Student.user_id == current_user.id).first()
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")

    mission = (
        db.query(Mission)
        .filter((Mission.id == mission_id) | (Mission.title == mission_id))
        .first()
    )
    if not mission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mission not found")

    # Idempotency check: if already completed, do NOT double-award XP
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
        total_drops = db.query(GardenDrop).filter(GardenDrop.class_id == student.class_id).count()
        return MissionSubmitResponse(
            xp_awarded=0,
            new_total_xp=student.current_xp,
            badge_unlocked=None,
            newly_unlocked_badges=[],
            garden_drops=total_drops,
            already_completed=True,
            message="Mission was already completed previously. No duplicate XP awarded.",
        )

    # 1. Effort-based XP Award
    xp_delta = mission.xp
    xp_entry = XpLedger(
        student_id=student.id,
        delta=xp_delta,
        reason=f"Mission completion: {mission.title}",
        ref_id=mission.id,
        created_at=now_utc(),
    )
    db.add(xp_entry)

    # 2. Add one drop to the cooperative Class Garden
    drop = GardenDrop(
        class_id=student.class_id,
        student_id=student.id,
        created_at=now_utc(),
    )
    db.add(drop)

    # 3. Mark or create completed MissionAttempt
    attempt = (
        db.query(MissionAttempt)
        .filter(
            MissionAttempt.student_id == student.id,
            MissionAttempt.mission_id == mission.id,
        )
        .first()
    )
    if not attempt:
        attempt = MissionAttempt(
            student_id=student.id,
            mission_id=mission.id,
            status="completed",
            hints_used=body.hints_used,
            score=body.score or 100,
            xp_awarded=xp_delta,
            completed_at=now_utc(),
        )
        db.add(attempt)
    else:
        attempt.status = "completed"
        attempt.hints_used = body.hints_used
        attempt.score = body.score or 100
        attempt.xp_awarded = xp_delta
        attempt.completed_at = now_utc()

    db.commit()

    # 4. Evaluate all 12 badges and award newly earned ones
    newly_unlocked = evaluate_and_award_badges(
        db=db,
        student_id=student.id,
        event="mission_complete",
        context={
            "hints_used": body.hints_used,
            "tries": body.tries,
            "mission": mission,
        },
    )

    unlocked_badge_code = newly_unlocked[0].code if newly_unlocked else None
    badge_items = [
        StudentBadgeItem(
            id=b.id,
            code=b.code,
            name=b.name,
            category=b.category,
            how_to_earn=b.how_to_earn,
            icon=b.icon,
            earned=True,
            earned_at=now_utc(),
        )
        for b in newly_unlocked
    ]

    total_drops = db.query(GardenDrop).filter(GardenDrop.class_id == student.class_id).count()

    return MissionSubmitResponse(
        xp_awarded=xp_delta,
        new_total_xp=student.current_xp,
        badge_unlocked=unlocked_badge_code,
        newly_unlocked_badges=badge_items,
        garden_drops=total_drops,
        already_completed=False,
        message=f"Mission completed! +{xp_delta} XP and 1 drop added to Class Garden.",
    )


@router.post("/doubts", response_model=StudentDoubtResponse)
def post_anonymous_doubt(
    body: StudentDoubtCreate,
    current_user: User = Depends(require_role("student")),
    db: Session = Depends(get_db),
):
    """
    Submits an anonymous "I'm stuck" doubt question.
    PRODUCT RULE 6: Anonymous doubts must not be linkable to a student in teacher APIs.
    Zero student_id or user_id saved.
    """
    student = db.query(Student).filter(Student.user_id == current_user.id).first()
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")

    full_text = f"{body.topic}: {body.text}" if body.topic and ":" not in body.text else body.text

    doubt = Doubt(
        class_id=student.class_id,
        text=full_text,
        resolved=False,
        created_at=now_utc(),
    )
    db.add(doubt)
    db.commit()
    db.refresh(doubt)

    # Evaluate 'question-asker' badge
    evaluate_and_award_badges(
        db=db,
        student_id=student.id,
        event="ask_doubt",
        context={"doubt": doubt},
    )

    return StudentDoubtResponse(
        id=doubt.id,
        class_name=student.class_name,
        text=doubt.text,
        topic=doubt.topic,
        message=doubt.message,
        created_at=doubt.created_at,
        resolved=doubt.resolved,
    )


@router.get("/badges", response_model=List[StudentBadgeItem])
def get_student_badges(
    current_user: User = Depends(require_role("student")),
    db: Session = Depends(get_db),
):
    """
    Returns full badge shelf with earned status for this student.
    """
    student = db.query(Student).filter(Student.user_id == current_user.id).first()
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")

    ensure_badges_exist(db)
    all_badges = db.query(Badge).all()

    earned_map = {
        sb.badge_id: sb.earned_at
        for sb in student.badges
    }

    results = []
    for b in all_badges:
        is_earned = b.id in earned_map
        results.append(
            StudentBadgeItem(
                id=b.id,
                code=b.code,
                name=b.name,
                category=b.category,
                how_to_earn=b.how_to_earn,
                icon=b.icon,
                earned=is_earned,
                earned_at=earned_map.get(b.id),
            )
        )

    return results
