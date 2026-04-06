import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.database import get_session
from app.main import app
from app.models import Base, Profile

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def db_engine():
    engine = create_async_engine(TEST_DB_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    # Seed default profile
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as s:
        s.add(Profile(id=1))
        await s.commit()
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def client(db_engine):
    factory = async_sessionmaker(db_engine, expire_on_commit=False)

    async def override_get_session():
        async with factory() as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac
    app.dependency_overrides.clear()
