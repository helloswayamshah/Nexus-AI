from typing import AsyncGenerator, Optional
from uuid import UUID

from fastapi import Depends, Header
from sqlalchemy import select
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.auth import decode_access_token
from app.core.errors import ForbiddenError, UnauthorizedError

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


async def init_engine(database_url: str) -> None:
    global _engine, _session_factory
    connect_args = {}
    if database_url.startswith("sqlite"):
        connect_args["check_same_thread"] = False
    _engine = create_async_engine(database_url, echo=False, connect_args=connect_args)
    _session_factory = async_sessionmaker(_engine, expire_on_commit=False, class_=AsyncSession)


async def dispose_engine() -> None:
    global _engine, _session_factory
    if _engine:
        await _engine.dispose()
    _engine = None
    _session_factory = None


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    if _session_factory is None:
        raise RuntimeError("Database engine not initialized")
    async with _session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_current_user(authorization: Optional[str] = Header(default=None)) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise UnauthorizedError()
    token = authorization.removeprefix("Bearer ").strip()
    try:
        payload = decode_access_token(token)
    except ValueError:
        raise UnauthorizedError("Invalid or expired token")
    return {"user_id": payload["sub"], "email": payload["email"]}


async def require_org_access(
    org_id: UUID,
    session: AsyncSession = Depends(get_async_session),
    user: dict = Depends(get_current_user),
) -> dict:
    from app.models.platform import OrgMember
    result = await session.execute(
        select(OrgMember).where(
            OrgMember.org_id == org_id,
            OrgMember.user_id == UUID(user["user_id"]),
        )
    )
    membership = result.scalar_one_or_none()
    if not membership:
        raise ForbiddenError("You are not a member of this org")
    return {**user, "org_role": membership.role}
