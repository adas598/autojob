from fastapi import APIRouter

from app.api import applications, jobs, profile

router = APIRouter()
router.include_router(profile.router, prefix="/profile", tags=["profile"])
router.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
router.include_router(applications.router, prefix="/applications", tags=["applications"])
