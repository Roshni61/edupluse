from typing import Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.models import User, Class, GardenDrop, Student
from app.schemas.schemas import ClassGardenResponse

router = APIRouter(prefix="/garden", tags=["Class Garden"])


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


@router.get("", response_model=ClassGardenResponse)
@router.get("/", response_model=ClassGardenResponse)
@router.get("/{class_name}", response_model=ClassGardenResponse)
def get_class_garden(
    class_name: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    PRODUCT RULE 2: No leaderboards. The Class Garden is cooperative and never names anyone.
    Returns aggregate progress for the entire class derived from garden_drops.
    """
    target_class_name = class_name
    if not target_class_name:
        # Check student profile class
        if current_user.student_profile:
            target_class_name = current_user.student_profile.class_name
        else:
            target_class_name = "9A"

    cls_obj = (
        db.query(Class)
        .filter(
            Class.school_id == current_user.school_id,
            Class.name == target_class_name,
        )
        .first()
    )
    total_drops = 0
    if cls_obj:
        total_drops = db.query(GardenDrop).filter(GardenDrop.class_id == cls_obj.id).count()

    pct = total_drops / 48.0
    stage = garden_stage(pct)

    return ClassGardenResponse(
        class_name=target_class_name,
        total_drops=total_drops,
        target_drops=48,
        stage=stage,
    )
