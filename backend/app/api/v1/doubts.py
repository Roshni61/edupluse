from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.api.deps import get_current_user, require_role
from app.db.session import get_db
from app.models.models import User, Class, Doubt
from app.schemas.schemas import AnonymousDoubtCreate, AnonymousDoubtResponse

router = APIRouter(prefix="/doubts", tags=["Doubts & Stuck"])


@router.post("", response_model=AnonymousDoubtResponse, status_code=status.HTTP_201_CREATED)
def submit_doubt(
    req: AnonymousDoubtCreate,
    current_user: User = Depends(require_role("student")),
    db: Session = Depends(get_db),
):
    """
    PRODUCT RULE 6: Anonymous 'I'm stuck'/doubt questions must not be linkable to a student in teacher APIs.
    The database record intentionally omits any user_id or student_id FK.
    """
    cls_obj = (
        db.query(Class)
        .filter(
            Class.school_id == current_user.school_id,
            Class.name == req.class_name,
        )
        .first()
    )
    if not cls_obj:
        cls_obj = db.query(Class).filter(Class.name == req.class_name).first()
        if not cls_obj:
            cls_obj = Class(school_id=current_user.school_id, name=req.class_name, grade="8")
            db.add(cls_obj)
            db.commit()
            db.refresh(cls_obj)

    text_content = f"{req.topic}: {req.message}" if req.message else req.topic

    doubt = Doubt(
        class_id=cls_obj.id,
        text=text_content,
        resolved=False,
    )
    db.add(doubt)
    db.commit()
    db.refresh(doubt)

    return AnonymousDoubtResponse(
        id=doubt.id,
        class_name=req.class_name,
        topic=req.topic,
        message=req.message,
        created_at=doubt.created_at,
    )


@router.get("/{class_name}", response_model=List[AnonymousDoubtResponse])
def get_class_doubts(
    class_name: str,
    current_user: User = Depends(require_role("teacher", "admin")),
    db: Session = Depends(get_db),
):
    """
    Teacher API for viewing doubts in the class.
    PRODUCT RULE 6: Absolutely no student identity information is present or linkable.
    """
    cls_obj = (
        db.query(Class)
        .filter(
            Class.school_id == current_user.school_id,
            Class.name == class_name,
        )
        .first()
    )
    if not cls_obj:
        return []

    doubts = (
        db.query(Doubt)
        .filter(Doubt.class_id == cls_obj.id)
        .order_by(Doubt.created_at.desc())
        .all()
    )
    res = []
    for d in doubts:
        topic_part = d.text.split(":", 1)[0].strip() if ":" in d.text else d.text
        msg_part = d.text.split(":", 1)[1].strip() if ":" in d.text else None
        res.append(
            AnonymousDoubtResponse(
                id=d.id,
                class_name=class_name,
                topic=topic_part,
                message=msg_part,
                created_at=d.created_at,
            )
        )
    return res
