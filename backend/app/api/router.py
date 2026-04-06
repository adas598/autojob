from fastapi import APIRouter

from app.api import profile

router = APIRouter()
router.include_router(profile.router, prefix="/profile", tags=["profile"])
