from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models.application import Application
from app.schemas.application import ApplicationOut, ApplicationUpdate

router = APIRouter()


@router.get("/", response_model=list[ApplicationOut])
async def list_applications(
    job_id: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    session: AsyncSession = Depends(get_session),
):
    q = select(Application)
    if job_id is not None:
        q = q.where(Application.job_id == job_id)
    q = q.offset(skip).limit(limit).order_by(Application.generated_at.desc())
    result = await session.execute(q)
    return result.scalars().all()


@router.get("/{application_id}", response_model=ApplicationOut)
async def get_application(
    application_id: str, session: AsyncSession = Depends(get_session)
):
    app = await session.get(Application, application_id)
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    return app


@router.patch("/{application_id}", response_model=ApplicationOut)
async def update_application(
    application_id: str,
    update: ApplicationUpdate,
    session: AsyncSession = Depends(get_session),
):
    app = await session.get(Application, application_id)
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    for field, value in update.model_dump(exclude_none=True).items():
        setattr(app, field, value)
    await session.commit()
    await session.refresh(app)
    return app
