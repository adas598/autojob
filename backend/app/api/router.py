from fastapi import APIRouter

from app.api.apply import router as applications_router
from app.api.jobs import router as jobs_router
from app.api.resume import router as resume_router
from app.api.settings import router as settings_router

api_router = APIRouter()
api_router.include_router(jobs_router)
api_router.include_router(resume_router)
api_router.include_router(applications_router)
api_router.include_router(settings_router)
