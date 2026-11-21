from typing import List
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.deps import get_current_user, require_role
from app.db.session import get_db
from app.models.models import (
    User,
    Student,
    Mission,
    MissionAttempt,
    GardenDrop,
    Badge,
    StudentBadge,
    XpLedger,
)
from app.schemas.schemas import (
    MissionResponse,
    MissionCompleteRequest,
    MissionCompleteResponse,
)
from app.services.effort_service import calculate_xp_award

router = APIRouter(prefix="/missions", tags=["Missions"])


@router.get("", response_model=List[MissionResponse])
def get_missions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    missions = db.query(Mission).filter(Mission.is_active == True).all()
    return [MissionResponse.model_validate(m) for m in missions]


@router.post("/complete", response_model=MissionCompleteResponse)
def complete_mission(
    req: MissionCompleteRequest,
    current_user: User = Depends(require_role("student")),
    db: Session = Depends(get_db),
):
    """
    PRODUCT RULE 1: XP is awarded for effort, never for marks. Same effort = same XP for every student.
    Server is the source of truth for XP and Class Garden updates.
    XP is recorded in xp_ledger, and drops are added to garden_drops.
    """
    student = db.query(Student).filter(Student.user_id == current_user.id).first()
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student profile not found")

    mission = db.query(Mission).filter(Mission.id == req.mission_id).first()
    if not mission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mission not found")

    # Award XP for effort (same XP regardless of attempts)
    xp_earned = calculate_xp_award(mission.xp)

    # Add entry to xp_ledger
    xp_entry = XpLedger(
        student_id=student.id,
        delta=xp_earned,
        reason=f"Completed mission: {mission.title}",
        ref_id=mission.id,
    )
    db.add(xp_entry)

    # Record mission attempt
    attempt = MissionAttempt(
        student_id=student.id,
        mission_id=mission.id,
        status="completed",
        hints_used=max(0, req.tries - 1),
        xp_awarded=xp_earned,
        completed_at=datetime.now(timezone.utc),
    )
    db.add(attempt)

    # Cooperative Class Garden: Every mission adds 1 drop anonymously
    drop = GardenDrop(
        class_id=student.class_id,
        student_id=None,  # Anonymous (PRODUCT RULE 2)
    )
    db.add(drop)

    # Check for unlocked badge
    unlocked_badge_name = None
    if mission.badge_id:
        existing = db.query(StudentBadge).filter(
            StudentBadge.student_id == student.id,
            StudentBadge.badge_id == mission.badge_id,
        ).first()
        if not existing:
            new_badge = StudentBadge(student_id=student.id, badge_id=mission.badge_id)
            db.add(new_badge)
            badge_obj = db.query(Badge).filter(Badge.id == mission.badge_id).first()
            unlocked_badge_name = badge_obj.name if badge_obj else mission.badge_id

    db.commit()
    db.refresh(student)

    return MissionCompleteResponse(
        xp_awarded=xp_earned,
        new_total_xp=student.current_xp,
        badge_unlocked=unlocked_badge_name,
        message="Mission completed! Effort rewarded and 1 drop added to the Class Garden.",
    )
