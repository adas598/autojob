from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models.job import Job, JobStatus, MatchScore
from app.schemas.job import JobOut, JobStatusUpdate

router = APIRouter()


@router.get("/", response_model=list[JobOut])
async def list_jobs(
    status: JobStatus | None = Query(None),
    match_score: MatchScore | None = Query(None),
    source: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    session: AsyncSession = Depends(get_session),
):
    q = select(Job)
    if status is not None:
        q = q.where(Job.status == status)
    if match_score is not None:
        q = q.where(Job.match_score == match_score)
    if source is not None:
        q = q.where(Job.source == source)
    q = q.offset(skip).limit(limit).order_by(Job.scraped_at.desc())
    result = await session.execute(q)
    return result.scalars().all()


@router.get("/{job_id}", response_model=JobOut)
async def get_job(job_id: str, session: AsyncSession = Depends(get_session)):
    job = await session.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.patch("/{job_id}/status", response_model=JobOut)
async def update_job_status(
    job_id: str,
    update: JobStatusUpdate,
    session: AsyncSession = Depends(get_session),
):
    job = await session.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    job.status = update.status
    await session.commit()
    await session.refresh(job)
    return job
