from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.deps import require_role
from app.core.config import settings
from app.db.session import get_db
from app.db.seed import seed_database
from app.models.models import User
from app.core.rate_limiter import login_rate_limiter

router = APIRouter(tags=["Demo"])


@router.post("/demo/reset")
def reset_demo(
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    """
    Reset demo data back to clean seeded state.
    - Admin-only
    - Disabled in production
    """
    if settings.ENVIRONMENT == "production" or not settings.DEMO_MODE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Demo reset is disabled in production.",
        )

    try:
        login_rate_limiter.reset()
        seed_database(db)
        return {"message": "Demo database successfully reset to clean state.", "success": True}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset demo database: {str(e)}",
        )
