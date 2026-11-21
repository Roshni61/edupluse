from typing import List, Callable, Any
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.core.exceptions import (
    PermissionDeniedException,
    SchoolMismatchException,
    ParentAccessDeniedException,
)
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.models import User, Student, ParentLink, ClassTeacher, Class

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    Extracts Bearer token from request, verifies signature and type='access',
    and retrieves active User from database.
    """
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    payload = decode_access_token(token, expected_type="access")
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials or token expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token subject")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user account")

    return user


def require_role(*allowed_roles: str) -> Callable:
    """
    ENGINEERING RULE: All endpoints are role-checked.
    """
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise PermissionDeniedException(
                f"Role '{current_user.role}' is not authorized. Required: {', '.join(allowed_roles)}"
            )
        return current_user

    return role_checker


def verify_school_scope(
    school_id: str,
    current_user: User = Depends(get_current_user)
) -> None:
    """
    ENGINEERING RULE: All endpoints are school-scoped.
    """
    if current_user.school_id != school_id:
        raise SchoolMismatchException()


def school_scope_filter(query: Any, model: Any, current_user: User) -> Any:
    """
    Applies school scope filtering to a query based on caller's school_id.
    """
    if hasattr(model, "school_id"):
        return query.filter(model.school_id == current_user.school_id)
    elif hasattr(model, "class_id"):
        # For tables linked through class_id (like Student, Doubt, Assessment)
        return query.join(Class, model.class_id == Class.id).filter(Class.school_id == current_user.school_id)
    return query


# --------------------------------------------------------------------------
# OWNERSHIP GUARDS:
# - A parent can only access students linked in parent_links
# - A student only their own record
# - A teacher only students in classes they teach
# - Admin only aggregates and school settings (no individual student detail)
# --------------------------------------------------------------------------

def verify_parent_access_to_student(
    student_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Student:
    """
    OWNERSHIP GUARD: A parent can only access students linked in parent_links.
    """
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")

    # Verify school boundary first
    if student.school_id != current_user.school_id:
        raise SchoolMismatchException()

    if current_user.role == "parent":
        link = db.query(ParentLink).filter(
            ParentLink.parent_user_id == current_user.id,
            ParentLink.student_id == student.id,
        ).first()
        if not link:
            raise ParentAccessDeniedException()

    return student


def verify_teacher_access_to_student(
    student_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Student:
    """
    OWNERSHIP GUARD: A teacher can only access students in classes they teach.
    """
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")

    # Verify school boundary
    if student.school_id != current_user.school_id:
        raise SchoolMismatchException()

    if current_user.role == "teacher":
        teaches_class = db.query(ClassTeacher).filter(
            ClassTeacher.teacher_id == current_user.id,
            ClassTeacher.class_id == student.class_id,
        ).first()
        if not teaches_class:
            raise PermissionDeniedException("Teachers may only access students in classes they teach.")

    return student


def verify_student_access(
    student_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Student:
    """
    OWNERSHIP GUARD: A student can only access their own record.
    """
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")

    if student.school_id != current_user.school_id:
        raise SchoolMismatchException()

    if current_user.role == "student" and student.user_id != current_user.id:
        raise PermissionDeniedException("Students may only access their own record.")

    return student


def verify_student_detail_access(
    student_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Student:
    """
    FULL OWNERSHIP GUARD FOR INDIVIDUAL STUDENT DETAIL:
    - Admin: FORBIDDEN (admin only aggregates and school settings, no individual student detail).
    - Teacher: only students in classes they teach.
    - Parent: only students linked in parent_links.
    - Student: FORBIDDEN (PRODUCT RULE 3: Students see growth only, never their support level. Support levels are teacher-only).
    """
    if current_user.role == "admin":
        raise PermissionDeniedException(
            "Administrators may only access school-level aggregates and settings, not individual student records."
        )
    elif current_user.role == "student":
        raise PermissionDeniedException(
            "Students are not authorized to view teacher diagnostic profiles. Use /students/growth to view your growth."
        )
    elif current_user.role == "teacher":
        return verify_teacher_access_to_student(student_id, current_user, db)
    elif current_user.role == "parent":
        return verify_parent_access_to_student(student_id, current_user, db)
    else:
        raise PermissionDeniedException("Unauthorized role.")
