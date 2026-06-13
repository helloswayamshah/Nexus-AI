import json
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_async_session, require_org_access
from app.core.crypto import encrypt, is_encrypted
from app.models.platform import PlatformLink
from app.schemas.platform_link import PlatformLinkCreate, PlatformLinkListResponse, PlatformLinkResponse

router = APIRouter()


def _to_response(link: PlatformLink) -> PlatformLinkResponse:
    return PlatformLinkResponse(
        id=link.id,
        org_id=link.org_id,
        platform=link.platform,
        external_id=link.external_id,
        display_name=link.display_name,
        created_at=link.created_at,
        updated_at=link.updated_at,
    )


@router.post("", response_model=PlatformLinkResponse, status_code=201)
async def create_platform_link(
    org_id: UUID,
    body: PlatformLinkCreate,
    session: AsyncSession = Depends(get_async_session),
    user: dict = Depends(require_org_access),
):
    creds_encrypted = None
    if body.credentials:
        creds_encrypted = encrypt(json.dumps(body.credentials))

    link = PlatformLink(
        org_id=org_id,
        platform=body.platform,
        external_id=body.external_id,
        display_name=body.display_name,
        credentials_encrypted=creds_encrypted,
        config_json=json.dumps(body.config) if body.config else None,
    )
    session.add(link)
    await session.flush()
    return _to_response(link)


@router.get("", response_model=PlatformLinkListResponse)
async def list_platform_links(
    org_id: UUID,
    session: AsyncSession = Depends(get_async_session),
    user: dict = Depends(require_org_access),
):
    rows = (await session.scalars(select(PlatformLink).where(PlatformLink.org_id == org_id))).all()
    total = await session.scalar(select(func.count(PlatformLink.id)).where(PlatformLink.org_id == org_id))
    return PlatformLinkListResponse(items=[_to_response(r) for r in rows], total=total)
