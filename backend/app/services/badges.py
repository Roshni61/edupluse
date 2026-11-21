"""
EduPulse Badge Engine.

Evaluates all 12 badge rules from BADGES in mock.ts:
1. first-step: Finish your very first mission.
2. showed-up: Complete 3 missions in one week.
3. try-again: Retry a question after a hint.
4. personal-best: Beat your own previous best score.
5. comeback: Return to missions after a break (>= 5 days).
6. topic-turnaround: Lift a weak topic by 15 points.
7. steady-week: Do something every school day for a week. Rest days never break it.
8. early-bird: Submit homework before the deadline 3 times.
9. helping-hand: Explain an idea to a classmate.
10. class-gardener: Water the Class Garden 5 times.
11. question-asker: Ask a doubt. Good questions count.
12. explorer: Try a Stretch mission.

PRODUCT RULE 1: Badges reward effort, growth, consistency, curiosity, and community, never top marks.
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from app.models.models import (
    Student,
    Badge,
    StudentBadge,
    MissionAttempt,
    Mission,
    HomeworkRecord,
    GardenDrop,
    Score,
)

logger = logging.getLogger("badge_engine")


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


BADGE_DEFINITIONS = [
    {
        "code": "first-step",
        "name": "First Step",
        "category": "Effort",
        "how_to_earn": "Finish your very first mission.",
        "icon": "Footprints",
    },
    {
        "code": "showed-up",
        "name": "Showed Up",
        "category": "Effort",
        "how_to_earn": "Complete 3 missions in one week.",
        "icon": "Sun",
    },
    {
        "code": "try-again",
        "name": "Tried Again",
        "category": "Effort",
        "how_to_earn": "Retry a question after a hint.",
        "icon": "RotateCcw",
    },
    {
        "code": "personal-best",
        "name": "Personal Best",
        "category": "Growth",
        "how_to_earn": "Beat your own previous best score.",
        "icon": "TrendingUp",
    },
    {
        "code": "comeback",
        "name": "Comeback",
        "category": "Growth",
        "how_to_earn": "Return to missions after a break.",
        "icon": "Rocket",
    },
    {
        "code": "topic-turnaround",
        "name": "Topic Turnaround",
        "category": "Growth",
        "how_to_earn": "Lift a weak topic by 15 points.",
        "icon": "Target",
    },
    {
        "code": "steady-week",
        "name": "Steady Week",
        "category": "Consistency",
        "how_to_earn": "Do something every school day for a week. Rest days never break it.",
        "icon": "CalendarCheck",
    },
    {
        "code": "early-bird",
        "name": "Early Bird",
        "category": "Consistency",
        "how_to_earn": "Submit homework before the deadline 3 times.",
        "icon": "Sunrise",
    },
    {
        "code": "helping-hand",
        "name": "Helping Hand",
        "category": "Community",
        "how_to_earn": "Explain an idea to a classmate.",
        "icon": "HeartHandshake",
    },
    {
        "code": "class-gardener",
        "name": "Class Gardener",
        "category": "Community",
        "how_to_earn": "Water the Class Garden 5 times.",
        "icon": "Sprout",
    },
    {
        "code": "question-asker",
        "name": "Question Asker",
        "category": "Curiosity",
        "how_to_earn": "Ask a doubt. Good questions count.",
        "icon": "MessageCircleQuestion",
    },
    {
        "code": "explorer",
        "name": "Explorer",
        "category": "Curiosity",
        "how_to_earn": "Try a Stretch mission.",
        "icon": "Compass",
    },
]


def ensure_badges_exist(db: Session) -> Dict[str, Badge]:
    """Ensures all 12 badge definitions exist in DB."""
    badges_map = {}
    for b_def in BADGE_DEFINITIONS:
        badge = db.query(Badge).filter(Badge.code == b_def["code"]).first()
        if not badge:
            badge = Badge(**b_def)
            db.add(badge)
            db.flush()
        badges_map[badge.code] = badge
    db.commit()
    return badges_map


def award_badge_to_student(db: Session, student_id: str, badge: Badge) -> Optional[Badge]:
    """Awards badge if not already earned."""
    existing = (
        db.query(StudentBadge)
        .filter(
            StudentBadge.student_id == student_id,
            StudentBadge.badge_id == badge.id,
        )
        .first()
    )
    if existing:
        return None

    sb = StudentBadge(
        student_id=student_id,
        badge_id=badge.id,
        earned_at=now_utc(),
    )
    db.add(sb)
    db.commit()
    return badge


def evaluate_and_award_badges(
    db: Session,
    student_id: str,
    event: str,
    context: Optional[Dict[str, Any]] = None,
) -> List[Badge]:
    """
    Evaluates all badge rules for the student and awards any newly earned badges.
    Returns list of newly unlocked badges.
    """
    context = context or {}
    badges_map = ensure_badges_exist(db)

    # Get student with relationships
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        return []

    # Already earned badge codes
    already_earned = {sb.badge.code for sb in student.badges if sb.badge}
    newly_unlocked: List[Badge] = []

    # Completed mission attempts
    completed_attempts = (
        db.query(MissionAttempt)
        .filter(
            MissionAttempt.student_id == student_id,
            MissionAttempt.status == "completed",
        )
        .order_by(MissionAttempt.completed_at.asc())
        .all()
    )
    total_completed = len(completed_attempts)

    # Rule 1: first-step - Finish your very first mission
    if "first-step" not in already_earned and total_completed >= 1:
        awarded = award_badge_to_student(db, student_id, badges_map["first-step"])
        if awarded:
            newly_unlocked.append(awarded)
            already_earned.add("first-step")

    # Rule 2: showed-up - Complete 3 missions in one week
    if "showed-up" not in already_earned and total_completed >= 3:
        week_ago = now_utc() - timedelta(days=7)
        recent_count = sum(
            1 for a in completed_attempts
            if a.completed_at and a.completed_at >= week_ago
        )
        if recent_count >= 3:
            awarded = award_badge_to_student(db, student_id, badges_map["showed-up"])
            if awarded:
                newly_unlocked.append(awarded)
                already_earned.add("showed-up")

    # Rule 3: try-again - Retry a question after a hint
    hints_used = context.get("hints_used", 0)
    tries = context.get("tries", 1)
    if "try-again" not in already_earned:
        if hints_used > 0 or tries > 1 or any(a.hints_used > 0 for a in completed_attempts):
            awarded = award_badge_to_student(db, student_id, badges_map["try-again"])
            if awarded:
                newly_unlocked.append(awarded)
                already_earned.add("try-again")

    # Rule 4: personal-best - Beat your own previous best score
    if "personal-best" not in already_earned:
        scores = student.scores_list
        if len(scores) >= 2:
            prev_max = max(scores[:-1])
            if scores[-1] > prev_max:
                awarded = award_badge_to_student(db, student_id, badges_map["personal-best"])
                if awarded:
                    newly_unlocked.append(awarded)
                    already_earned.add("personal-best")
        elif context.get("personal_best"):
            awarded = award_badge_to_student(db, student_id, badges_map["personal-best"])
            if awarded:
                newly_unlocked.append(awarded)
                already_earned.add("personal-best")

    # Rule 5: comeback - Return to missions after a break (>= 5 days)
    if "comeback" not in already_earned and total_completed >= 2:
        for idx in range(1, total_completed):
            prev_at = completed_attempts[idx - 1].completed_at
            curr_at = completed_attempts[idx].completed_at
            if prev_at and curr_at and (curr_at - prev_at).days >= 5:
                awarded = award_badge_to_student(db, student_id, badges_map["comeback"])
                if awarded:
                    newly_unlocked.append(awarded)
                    already_earned.add("comeback")
                break

    # Rule 6: topic-turnaround - Lift a weak topic by 15 points
    if "topic-turnaround" not in already_earned:
        scores = student.scores_list
        if len(scores) >= 2:
            min_score = min(scores[:-1])
            if scores[-1] - min_score >= 15:
                awarded = award_badge_to_student(db, student_id, badges_map["topic-turnaround"])
                if awarded:
                    newly_unlocked.append(awarded)
                    already_earned.add("topic-turnaround")
        elif context.get("topic_turnaround"):
            awarded = award_badge_to_student(db, student_id, badges_map["topic-turnaround"])
            if awarded:
                newly_unlocked.append(awarded)
                already_earned.add("topic-turnaround")

    # Rule 7: steady-week - Do something every school day for a week. Rest days never break it.
    if "steady-week" not in already_earned:
        # Check attendance or activity in school days
        if student.attendance:
            last_5 = student.attendance[-5:]
            if len(last_5) >= 5 and all(a.present for a in last_5):
                awarded = award_badge_to_student(db, student_id, badges_map["steady-week"])
                if awarded:
                    newly_unlocked.append(awarded)
                    already_earned.add("steady-week")
        elif total_completed >= 5:
            awarded = award_badge_to_student(db, student_id, badges_map["steady-week"])
            if awarded:
                newly_unlocked.append(awarded)
                already_earned.add("steady-week")

    # Rule 8: early-bird - Submit homework before the deadline 3 times
    if "early-bird" not in already_earned:
        on_time_count = (
            db.query(HomeworkRecord)
            .filter(
                HomeworkRecord.student_id == student_id,
                HomeworkRecord.status == "on_time",
            )
            .count()
        )
        if on_time_count >= 3:
            awarded = award_badge_to_student(db, student_id, badges_map["early-bird"])
            if awarded:
                newly_unlocked.append(awarded)
                already_earned.add("early-bird")

    # Rule 9: helping-hand - Explain an idea to a classmate
    mission = context.get("mission")
    if "helping-hand" not in already_earned:
        if (mission and mission.kind == "help") or event == "peer_help":
            awarded = award_badge_to_student(db, student_id, badges_map["helping-hand"])
            if awarded:
                newly_unlocked.append(awarded)
                already_earned.add("helping-hand")

    # Rule 10: class-gardener - Water the Class Garden 5 times
    if "class-gardener" not in already_earned:
        drops_count = (
            db.query(GardenDrop)
            .filter(GardenDrop.student_id == student_id)
            .count()
        )
        if drops_count >= 5 or total_completed >= 5:
            awarded = award_badge_to_student(db, student_id, badges_map["class-gardener"])
            if awarded:
                newly_unlocked.append(awarded)
                already_earned.add("class-gardener")

    # Rule 11: question-asker - Ask a doubt. Good questions count.
    if "question-asker" not in already_earned:
        if event == "ask_doubt" or (mission and mission.kind == "ask"):
            awarded = award_badge_to_student(db, student_id, badges_map["question-asker"])
            if awarded:
                newly_unlocked.append(awarded)
                already_earned.add("question-asker")

    # Rule 12: explorer - Try a Stretch mission
    if "explorer" not in already_earned:
        if mission and getattr(mission, "tier", "") == "Stretch":
            awarded = award_badge_to_student(db, student_id, badges_map["explorer"])
            if awarded:
                newly_unlocked.append(awarded)
                already_earned.add("explorer")

    return newly_unlocked
