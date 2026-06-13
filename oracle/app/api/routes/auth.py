from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_async_session
from app.core.auth import create_access_token, hash_password, verify_password
from app.core.errors import ConflictError, UnauthorizedError
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, RegisterResponse, TokenResponse

router = APIRouter()


@router.post("/register", response_model=RegisterResponse, status_code=201)
async def register(body: RegisterRequest, session: AsyncSession = Depends(get_async_session)):
    existing = await session.scalar(select(User).where(User.email == body.email))
    if existing:
        raise ConflictError(f"Email already registered: {body.email}")
    user = User(email=body.email, name=body.display_name, password_hash=hash_password(body.password))
    session.add(user)
    await session.flush()
    return RegisterResponse(user_id=str(user.id), email=user.email, display_name=user.name)


@router.post("/token", response_model=TokenResponse)
async def login(body: LoginRequest, session: AsyncSession = Depends(get_async_session)):
    user = await session.scalar(select(User).where(User.email == body.email))
    if not user or not user.password_hash or not verify_password(body.password, user.password_hash):
        raise UnauthorizedError("Invalid email or password")
    token = create_access_token(str(user.id), user.email)
    return TokenResponse(access_token=token)
