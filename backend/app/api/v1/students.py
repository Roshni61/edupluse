from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.deps import (
    get_current_user,
    require_role,
    verify_parent_access_to_student,
    verify_student_detail_access,
)
from app.core.exceptions import PermissionDeniedException
from app.db.session import get_db
from app.models.models import User, Student, Class, ClassTeacher
from app.schemas.schemas import (
    StudentGrowthView,
    StudentTeacherView,
    StudentParentView,
)
from app.services.audit_service import log_sensitive_access

router = APIRouter(prefix="/students", tags=["Students"])


@router.get("/growth", response_model=StudentGrowthView)
def get_student_growth(
    current_user: User = Depends(require_role("student")),
    db: Session = Depends(get_db),
):
    """
    PRODUCT RULE 3: Students see growth only, never their support level.
    OWNERSHIP GUARD: Students access only their own record.
    """
    student = db.query(Student).filter(Student.user_id == current_user.id).first()
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student profile not found")

    return StudentGrowthView.model_validate(student)


@router.get("/teacher-view", response_model=List[StudentTeacherView])
def get_teacher_students(
    class_name: str = "9A",
    current_user: User = Depends(require_role("teacher", "admin")),
    db: Session = Depends(get_db),
):
    """
    Teacher and Admin view: School-scoped early warning and support levels.
    OWNERSHIP GUARD:
    - Teacher only views classes they teach.
    - Admin views aggregate class lists for their school.
    PRODUCT RULE 7: Every sensitive read/write by teacher/admin is written to an audit log.
    """
    cls = (
        db.query(Class)
        .filter(Class.school_id == current_user.school_id, Class.name == class_name)
        .first()
    )
    if not cls:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Class {class_name} not found")

    if current_user.role == "teacher":
        teaches_class = db.query(ClassTeacher).filter(
            ClassTeacher.teacher_id == current_user.id,
            ClassTeacher.class_id == cls.id,
        ).first()
        if not teaches_class:
            raise PermissionDeniedException(f"Teachers may only access classes they teach (not class {class_name}).")

    students = (
        db.query(Student)
        .join(Class, Student.class_id == Class.id)
        .filter(
            Class.school_id == current_user.school_id,
            Class.name == class_name,
        )
        .all()
    )

    # Log audit entry for reading sensitive support levels
    log_sensitive_access(
        db=db,
        school_id=current_user.school_id,
        actor_id=current_user.id,
        actor_role=current_user.role,
        action="READ_CLASS_SUPPORT_LIST",
        resource_type="student_support_levels",
        resource_id=class_name,
        details={"class": class_name, "count": len(students)},
    )

    return [StudentTeacherView.model_validate(s) for s in students]


@router.get("/{student_id}", response_model=StudentTeacherView)
def get_student_detail(
    student_id: str,
    student: Student = Depends(verify_student_detail_access),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Detailed student view with Change-from-Self analysis.
    OWNERSHIP GUARD:
    - Teacher: only students in classes they teach.
    - Admin: FORBIDDEN (admin only aggregates and school settings, no individual student detail).
    PRODUCT RULE 7: Audited sensitive read.
    """
    log_sensitive_access(
        db=db,
        school_id=current_user.school_id,
        actor_id=current_user.id,
        actor_role=current_user.role,
        action="READ_STUDENT_DETAIL",
        resource_type="student",
        resource_id=student.id,
        details={"student_name": student.name, "support_level": student.support_level},
    )

    return StudentTeacherView.model_validate(student)


@router.get("/parent/child/{student_id}", response_model=StudentParentView)
def get_parent_child(
    student_id: str,
    student: Student = Depends(verify_parent_access_to_student),
):
    """
    ENGINEERING RULE: Parents see only their own child(ren).
    OWNERSHIP GUARD: Parent can only access students linked in parent_links.
    """
    return StudentParentView.model_validate(student)
