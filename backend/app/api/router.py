from fastapi import APIRouter

from app.api import applied_history, applications, jobs, profile, sources

router = APIRouter()
router.include_router(profile.router, prefix="/profile", tags=["profile"])
router.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
router.include_router(applications.router, prefix="/applications", tags=["applications"])
router.include_router(sources.router, prefix="/sources", tags=["sources"])
router.include_router(applied_history.router, prefix="/applied-history", tags=["applied-history"])
