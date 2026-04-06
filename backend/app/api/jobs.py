import uuid
from math import ceil

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.database import get_db
from app.models.base import JobType, Portal, Seniority, VisaStatus
from app.models.job import Job
from app.models.job_score import JobScore
from app.schemas.job import JobListResponse, JobResponse

router = APIRouter(prefix="/jobs", tags=["jobs"])

SORTABLE_COLUMNS = {"scraped_at", "salary_min", "salary_max", "title", "company"}
DEFAULT_MATCH_THRESHOLD = 50


def _latest_score_subquery():
    """Subquery returning the latest JobScore per job_id."""
    return (
        select(
            JobScore.job_id,
            JobScore.overall_score,
            JobScore.rubric_breakdown,
            JobScore.reasoning,
        )
        .distinct(JobScore.job_id)
        .order_by(JobScore.job_id, JobScore.scored_at.desc())
        .subquery("latest_score")
    )


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
    latest_score = _latest_score_subquery()

    query = (
        select(
            Job,
            latest_score.c.overall_score,
            latest_score.c.rubric_breakdown,
            latest_score.c.reasoning,
        )
        .outerjoin(latest_score, Job.id == latest_score.c.job_id)
    )

    # Job-level filters
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

    # Score-level filters
    if not show_all:
        query = query.where(
            (latest_score.c.overall_score >= DEFAULT_MATCH_THRESHOLD)
            | (latest_score.c.overall_score.is_(None))
        )
    if score_min is not None:
        query = query.where(latest_score.c.overall_score >= score_min)
    if score_max is not None:
        query = query.where(latest_score.c.overall_score <= score_max)

    # Sorting
    if sort_by == "overall_score":
        sort_column = latest_score.c.overall_score
    elif sort_by in SORTABLE_COLUMNS:
        sort_column = getattr(Job, sort_by)
    else:
        sort_column = Job.scraped_at

    if sort_order == "asc":
        query = query.order_by(sort_column.asc().nullslast())
    else:
        query = query.order_by(sort_column.desc().nullslast())

    # Count
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    # Paginate
    offset = (page - 1) * per_page
    query = query.offset(offset).limit(per_page)

    result = await db.execute(query)
    rows = result.all()

    items = []
    for job, overall_score, rubric_breakdown, reasoning in rows:
        item = JobResponse.model_validate(job)
        item.overall_score = overall_score
        item.rubric_breakdown = rubric_breakdown
        item.reasoning = reasoning
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
    latest_score = _latest_score_subquery()

    query = (
        select(
            Job,
            latest_score.c.overall_score,
            latest_score.c.rubric_breakdown,
            latest_score.c.reasoning,
        )
        .outerjoin(latest_score, Job.id == latest_score.c.job_id)
        .where(Job.id == job_id)
    )

    result = await db.execute(query)
    row = result.one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Job not found")

    job, overall_score, rubric_breakdown, reasoning = row
    item = JobResponse.model_validate(job)
    item.overall_score = overall_score
    item.rubric_breakdown = rubric_breakdown
    item.reasoning = reasoning
    return item
