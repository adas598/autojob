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
    query = (
        select(Application, Job.title, Job.company)
        .outerjoin(Job, Application.job_id == Job.id)
        .order_by(Application.updated_at.desc())
    )
    result = await db.execute(query)
    rows = result.all()

    items = []
    for app_record, job_title, job_company in rows:
        item = ApplicationResponse.model_validate(app_record)
        item.job_title = job_title
        item.job_company = job_company
        items.append(item)

    return ApplicationListResponse(items=items)


@router.patch("/{application_id}", response_model=ApplicationResponse)
async def update_application_status(
    application_id: uuid.UUID,
    body: ApplicationStatusUpdate,
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(Application, Job.title, Job.company)
        .outerjoin(Job, Application.job_id == Job.id)
        .where(Application.id == application_id)
    )
    result = await db.execute(query)
    row = result.one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Application not found")

    app_record, job_title, job_company = row
    app_record.status = body.status
    await db.commit()
    await db.refresh(app_record)

    item = ApplicationResponse.model_validate(app_record)
    item.job_title = job_title
    item.job_company = job_company
    return item
