import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.application import Application
from app.models.job import Job
from app.schemas.application import (
    ApplicationListResponse,
    ApplicationResponse,
    ApplicationStatusUpdate,
)

router = APIRouter(prefix="/applications", tags=["applications"])


@router.get("", response_model=ApplicationListResponse)
async def list_applications(db: AsyncSession = Depends(get_db)):
    query = select(Application).order_by(Application.updated_at.desc())
    result = await db.execute(query)
    apps = result.scalars().all()

    items = []
    for app_record in apps:
        item = ApplicationResponse.model_validate(app_record)
        job_result = await db.execute(select(Job).where(Job.id == app_record.job_id))
        job = job_result.scalar_one_or_none()
        if job:
            item.job_title = job.title
            item.job_company = job.company
        items.append(item)

    return ApplicationListResponse(items=items)


@router.patch("/{application_id}", response_model=ApplicationResponse)
async def update_application_status(
    application_id: uuid.UUID,
    body: ApplicationStatusUpdate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Application).where(Application.id == application_id)
    )
    app_record = result.scalar_one_or_none()
    if not app_record:
        raise HTTPException(status_code=404, detail="Application not found")

    app_record.status = body.status
    await db.commit()
    await db.refresh(app_record)

    item = ApplicationResponse.model_validate(app_record)
    job_result = await db.execute(select(Job).where(Job.id == app_record.job_id))
    job = job_result.scalar_one_or_none()
    if job:
        item.job_title = job.title
        item.job_company = job.company
    return item
