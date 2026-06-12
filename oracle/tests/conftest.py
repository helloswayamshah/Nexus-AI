"""
Shared pytest fixtures for all test layers.

Fixture scoping:
  engine        — session-scoped: one SQLite engine per pytest run
  tables        — session-scoped: creates/drops schema once
  db_session    — function-scoped: each test gets a clean transaction, rolled back after
  app           — session-scoped: FastAPI app with engine overridden to test DB
  client        — function-scoped: AsyncClient per test, shares app
"""

import os
import pytest
import pytest_asyncio

# Force SQLite before any app code imports config
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test.db")
os.environ.setdefault("JWT_SECRET", "test-secret")
os.environ.setdefault("ENCRYPTION_KEY", "a" * 64)  # 64 hex chars = valid 32-byte key

from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.models import Base
from app.main import create_app
from app.api import deps


TEST_DB_URL = "sqlite+aiosqlite:///./test.db"


# ── Engine & schema ───────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def engine():
    return create_async_engine(TEST_DB_URL, connect_args={"check_same_thread": False})


@pytest_asyncio.fixture(scope="session")
async def tables(engine):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


# ── Per-test session — rolls back after every test ────────────────────────

@pytest_asyncio.fixture
async def db_session(engine, tables) -> AsyncSession:
    """
    Wraps each test in a savepoint. The outer transaction is never committed,
    so every test starts with a clean slate without recreating the schema.
    """
    async with engine.connect() as conn:
        await conn.begin()
        session_factory = async_sessionmaker(
            bind=conn, expire_on_commit=False, class_=AsyncSession
        )
        async with session_factory() as session:
            yield session
        await conn.rollback()


# ── FastAPI app + HTTP client ─────────────────────────────────────────────

@pytest.fixture(scope="session")
def app(engine):
    """FastAPI app with its DB engine replaced by the test engine."""
    _app = create_app()

    # Override the session factory to use the test engine
    test_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    async def override_session():
        async with test_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    _app.dependency_overrides[deps.get_async_session] = override_session
    return _app


@pytest_asyncio.fixture
async def client(app, tables) -> AsyncClient:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac
