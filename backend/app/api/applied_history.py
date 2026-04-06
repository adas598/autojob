from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models.applied_history import AppliedHistory
from app.schemas.applied_history import (
    AppliedHistoryCreate,
    AppliedHistoryOut,
    AppliedHistoryUpdate,
)

router = APIRouter()


@router.get("/", response_model=list[AppliedHistoryOut])
async def list_applied_history(
    job_id: str | None = Query(None),
    session: AsyncSession = Depends(get_session),
):
    q = select(AppliedHistory)
    if job_id is not None:
        q = q.where(AppliedHistory.job_id == job_id)
    q = q.order_by(AppliedHistory.changed_at.desc())
    result = await session.execute(q)
    return result.scalars().all()


@router.post("/", response_model=AppliedHistoryOut, status_code=201)
async def create_applied_history(
    body: AppliedHistoryCreate, session: AsyncSession = Depends(get_session)
):
    entry = AppliedHistory(**body.model_dump())
    session.add(entry)
    await session.commit()
    await session.refresh(entry)
    return entry


@router.patch("/{entry_id}", response_model=AppliedHistoryOut)
async def update_applied_history(
    entry_id: str,
    update: AppliedHistoryUpdate,
    session: AsyncSession = Depends(get_session),
):
    entry = await session.get(AppliedHistory, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    for field, value in update.model_dump(exclude_none=True).items():
        setattr(entry, field, value)
    await session.commit()
    await session.refresh(entry)
    return entry
