from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.router import router
from app.database import AsyncSessionLocal, engine
from app.models import Base, Profile


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with AsyncSessionLocal() as session:
        if not await session.get(Profile, 1):
            session.add(Profile(id=1))
            await session.commit()
    yield
    await engine.dispose()


app = FastAPI(title="AutoJob", version="0.1.0", lifespan=lifespan)
app.include_router(router)


@app.get("/health")
async def health():
    return {"status": "ok"}
