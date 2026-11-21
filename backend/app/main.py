import os
import logging
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.core.config import settings
from app.db.session import engine, Base
from app.api.v1.api import api_router
from app.api.v1.health import health_check

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("edupulse")

if os.environ.get("VERCEL"):
    uploads_dir = Path("/tmp") / "uploads"
else:
    uploads_dir = Path(__file__).resolve().parent.parent / "uploads"
uploads_dir.mkdir(parents=True, exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure tables exist in dev/fallback
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables initialized successfully.")

        # Auto-seed database if empty (ensures demo works out of the box in serverless/cloud)
        from app.db.session import SessionLocal
        from app.models.models import User
        from app.db.seed import seed_database
        with SessionLocal() as db:
            if not db.query(User).first():
                logger.info("No users found in database. Running seed...")
                seed_database(db)
                logger.info("Auto-seed completed successfully.")
    except Exception as e:
        logger.warning(f"Could not connect to database on startup: {e}. /health endpoint remains functional.")
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Backend API for EduPulse - Fair gamification, early warning, and respectful parent communication.",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static file serving for uploads (voice notes, media)
app.mount("/uploads", StaticFiles(directory=str(uploads_dir)), name="uploads")

# Direct root /health endpoint
app.add_api_route("/health", health_check, methods=["GET"], tags=["Health"])

# Direct root /demo/reset endpoint (also available at /api/v1/demo/reset)
from app.api.v1.demo import router as demo_router
from app.api.v1.admin import router as admin_router
from app.api.v1.teacher import router as teacher_router
from app.api.v1.student import router as student_router
from app.api.v1.garden import router as garden_router
from app.api.v1.parent import router as parent_router, sms_router, voice_router
app.include_router(demo_router)
app.include_router(admin_router)
app.include_router(teacher_router)
app.include_router(student_router)
app.include_router(garden_router, prefix="/class")
app.include_router(parent_router)
app.include_router(sms_router)
app.include_router(voice_router)

# API v1 routes
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/", tags=["Root"])
def root():
    return {
        "message": "Welcome to EduPulse API",
        "docs": "/docs",
        "health": "/health",
        "version": "0.1.0",
    }
