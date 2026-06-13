import re
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_async_session, get_current_user
from app.core.errors import ConflictError, NotFoundError
from app.models.org import Org
from app.models.platform import OrgMember
from app.models.enums import OrgRole
from app.schemas.org import OrgCreate, OrgResponse

router = APIRouter()


def _slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


@router.post("", response_model=OrgResponse, status_code=201)
async def create_org(
    body: OrgCreate,
    session: AsyncSession = Depends(get_async_session),
    user: dict = Depends(get_current_user),
):
    slug = body.slug or _slugify(body.name)
    existing = await session.scalar(select(Org).where(Org.slug == slug))
    if existing:
        raise ConflictError(f"Org slug already taken: {slug}")
    org = Org(slug=slug, display_name=body.name)
    session.add(org)
    await session.flush()
    membership = OrgMember(org_id=org.id, user_id=UUID(user["user_id"]), role=OrgRole.OWNER)
    session.add(membership)
    return OrgResponse(id=org.id, name=org.display_name, slug=org.slug, created_at=org.created_at)


@router.get("/{org_id}", response_model=OrgResponse)
async def get_org(
    org_id: UUID,
    session: AsyncSession = Depends(get_async_session),
    user: dict = Depends(get_current_user),
):
    org = await session.get(Org, org_id)
    if not org:
        raise NotFoundError("Org", str(org_id))
    return OrgResponse(id=org.id, name=org.display_name, slug=org.slug, created_at=org.created_at)
