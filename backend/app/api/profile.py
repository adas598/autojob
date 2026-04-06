from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models.profile import Profile
from app.schemas.profile import ProfileOut, ProfileUpdate

router = APIRouter()


@router.get("/", response_model=ProfileOut)
async def get_profile(session: AsyncSession = Depends(get_session)):
    profile = await session.get(Profile, 1)
    return profile


@router.put("/", response_model=ProfileOut)
async def update_profile(
    update: ProfileUpdate, session: AsyncSession = Depends(get_session)
):
    profile = await session.get(Profile, 1)
    for field, value in update.model_dump(exclude_none=True).items():
        setattr(profile, field, value)
    await session.commit()
    await session.refresh(profile)
    return profile
