import uuid
from math import ceil

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.base import JobType, Portal, Seniority, VisaStatus
from app.models.job import Job
from app.models.job_score import JobScore
from app.schemas.job import JobListResponse, JobResponse

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("", response_model=JobListResponse)
async def list_jobs(
    location: str | None = None,
    salary_min: int | None = None,
    salary_max: int | None = None,
    job_type: JobType | None = None,
    seniority: Seniority | None = None,
    visa_status: VisaStatus | None = None,
    portal: Portal | None = None,
    score_min: int | None = None,
    score_max: int | None = None,
    show_all: bool = False,
    sort_by: str = "scraped_at",
    sort_order: str = "desc",
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    query = select(Job)

    if location:
        query = query.where(Job.location.ilike(f"%{location}%"))
    if salary_min is not None:
        query = query.where(Job.salary_max >= salary_min)
    if salary_max is not None:
        query = query.where(Job.salary_min <= salary_max)
    if job_type:
        query = query.where(Job.job_type == job_type)
    if seniority:
        query = query.where(Job.seniority == seniority)
    if visa_status:
        query = query.where(Job.visa_status.any(visa_status))
    if portal:
        query = query.where(Job.portal == portal)

    sort_column = getattr(Job, sort_by, Job.scraped_at)
    if sort_order == "asc":
        query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(sort_column.desc())

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    offset = (page - 1) * per_page
    query = query.offset(offset).limit(per_page)

    result = await db.execute(query)
    jobs = result.scalars().all()

    items = []
    for job in jobs:
        item = JobResponse.model_validate(job)
        score_query = (
            select(JobScore)
            .where(JobScore.job_id == job.id)
            .order_by(JobScore.scored_at.desc())
            .limit(1)
        )
        score_result = await db.execute(score_query)
        score = score_result.scalar_one_or_none()
        if score:
            item.overall_score = score.overall_score
            item.rubric_breakdown = score.rubric_breakdown
            item.reasoning = score.reasoning
        items.append(item)

    return JobListResponse(
        total=total,
        page=page,
        per_page=per_page,
        pages=ceil(total / per_page) if total > 0 else 0,
        items=items,
    )


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(job_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    item = JobResponse.model_validate(job)
    score_query = (
        select(JobScore)
        .where(JobScore.job_id == job.id)
        .order_by(JobScore.scored_at.desc())
        .limit(1)
    )
    score_result = await db.execute(score_query)
    score = score_result.scalar_one_or_none()
    if score:
        item.overall_score = score.overall_score
        item.rubric_breakdown = score.rubric_breakdown
        item.reasoning = score.reasoning
    return item
