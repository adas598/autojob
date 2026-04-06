from fastapi import APIRouter

from app.api import jobs, profile

router = APIRouter()
router.include_router(profile.router, prefix="/profile", tags=["profile"])
router.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
