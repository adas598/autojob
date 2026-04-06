from fastapi import APIRouter

from app.api.jobs import router as jobs_router
from app.api.resume import router as resume_router

api_router = APIRouter()
api_router.include_router(jobs_router)
api_router.include_router(resume_router)
