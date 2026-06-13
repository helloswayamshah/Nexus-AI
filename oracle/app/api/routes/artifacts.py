from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_async_session, require_org_access
from app.models.artifact import Artifact
from app.models.enums import ArtifactType
from app.schemas.artifact import ArtifactListResponse, ArtifactResponse

router = APIRouter()


@router.get("", response_model=ArtifactListResponse)
async def list_artifacts(
    org_id: UUID,
    artifact_type: Optional[ArtifactType] = Query(default=None),
    event_id: Optional[UUID] = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_async_session),
    user: dict = Depends(require_org_access),
):
    q = select(Artifact).where(Artifact.org_id == org_id)
    if artifact_type:
        q = q.where(Artifact.artifact_type == artifact_type)
    if event_id:
        q = q.where(Artifact.event_id == event_id)

    total = await session.scalar(select(func.count()).select_from(q.subquery()))
    rows = (await session.scalars(q.order_by(Artifact.created_at.desc()).limit(limit).offset(offset))).all()

    items = [ArtifactResponse.from_orm_with_meta(r) for r in rows]
    return ArtifactListResponse(items=items, total=total, limit=limit, offset=offset, has_more=(offset + limit) < total)
