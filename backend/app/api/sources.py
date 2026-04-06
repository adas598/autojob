from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models.source import Source
from app.schemas.source import SourceCreate, SourceOut, SourceUpdate

router = APIRouter()


@router.get("/", response_model=list[SourceOut])
async def list_sources(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Source).order_by(Source.name))
    return result.scalars().all()


@router.post("/", response_model=SourceOut, status_code=201)
async def create_source(
    body: SourceCreate, session: AsyncSession = Depends(get_session)
):
    source = Source(**body.model_dump())
    session.add(source)
    await session.commit()
    await session.refresh(source)
    return source


@router.patch("/{source_id}", response_model=SourceOut)
async def update_source(
    source_id: str,
    update: SourceUpdate,
    session: AsyncSession = Depends(get_session),
):
    source = await session.get(Source, source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    for field, value in update.model_dump(exclude_none=True).items():
        setattr(source, field, value)
    await session.commit()
    await session.refresh(source)
    return source


@router.delete("/{source_id}", status_code=204)
async def delete_source(source_id: str, session: AsyncSession = Depends(get_session)):
    source = await session.get(Source, source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    await session.delete(source)
    await session.commit()
