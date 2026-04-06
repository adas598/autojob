import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.resume import Resume
from app.schemas.resume import ResumeListResponse, ResumeResponse, ResumeUploadResponse

router = APIRouter(prefix="/resume", tags=["resume"])


@router.post("/upload", response_model=ResumeUploadResponse)
async def upload_resume(file: UploadFile, db: AsyncSession = Depends(get_db)):
    if not file.filename or not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")

    pdf_bytes = await file.read()
    await db.execute(update(Resume).values(is_active=False))

    resume = Resume(
        file_name=file.filename,
        raw_text="",
        parsed_skills=[],
        parsed_experience=[],
        parsed_education=[],
        pdf_blob=pdf_bytes,
        is_active=True,
    )
    db.add(resume)
    await db.commit()
    await db.refresh(resume)

    return ResumeUploadResponse(
        id=resume.id,
        file_name=resume.file_name,
        parsed_skills=resume.parsed_skills,
        parsed_experience=resume.parsed_experience,
        parsed_education=resume.parsed_education,
        is_active=resume.is_active,
    )


@router.get("/active", response_model=ResumeResponse)
async def get_active_resume(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Resume).where(Resume.is_active == True))
    resume = result.scalar_one_or_none()
    if not resume:
        raise HTTPException(status_code=404, detail="No active resume found")
    return ResumeResponse.model_validate(resume)


@router.get("", response_model=ResumeListResponse)
async def list_resumes(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Resume).order_by(Resume.created_at.desc()))
    resumes = result.scalars().all()
    return ResumeListResponse(
        items=[ResumeResponse.model_validate(r) for r in resumes]
    )


@router.post("/{resume_id}/activate", response_model=ResumeResponse)
async def activate_resume(resume_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Resume).where(Resume.id == resume_id))
    resume = result.scalar_one_or_none()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    await db.execute(update(Resume).values(is_active=False))
    resume.is_active = True
    await db.commit()
    await db.refresh(resume)
    return ResumeResponse.model_validate(resume)
