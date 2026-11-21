from fastapi import APIRouter
from app.api.v1 import health, auth, students, student, missions, garden, doubts, bookings, demo, teacher, parent, admin

api_router = APIRouter()

api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(admin.router)
api_router.include_router(teacher.router)
api_router.include_router(student.router)
api_router.include_router(students.router)
api_router.include_router(missions.router)
api_router.include_router(garden.router)
api_router.include_router(doubts.router)
api_router.include_router(bookings.router)
api_router.include_router(parent.router)
api_router.include_router(parent.sms_router)
api_router.include_router(parent.voice_router)
api_router.include_router(demo.router)
