from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_async_session, require_org_access
from app.core.errors import NotFoundError
from app.models.artifact import ActionItem
from app.models.enums import ActionItemStatus
from app.schemas.action_item import ActionItemListResponse, ActionItemResponse, ActionItemUpdate

router = APIRouter()


@router.get("", response_model=ActionItemListResponse)
async def list_action_items(
    org_id: UUID,
    status: Optional[ActionItemStatus] = Query(default=None),
    assignee_id: Optional[UUID] = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_async_session),
    user: dict = Depends(require_org_access),
):
    q = select(ActionItem).where(ActionItem.org_id == org_id)
    if status:
        q = q.where(ActionItem.status == status)
    if assignee_id:
        q = q.where(ActionItem.assignee_id == assignee_id)

    total = await session.scalar(select(func.count()).select_from(q.subquery()))
    rows = (await session.scalars(q.order_by(ActionItem.created_at.desc()).limit(limit).offset(offset))).all()

    items = [ActionItemResponse.model_validate(r) for r in rows]
    return ActionItemListResponse(items=items, total=total, limit=limit, offset=offset, has_more=(offset + limit) < total)


@router.patch("/{item_id}", response_model=ActionItemResponse)
async def update_action_item(
    org_id: UUID,
    item_id: UUID,
    body: ActionItemUpdate,
    session: AsyncSession = Depends(get_async_session),
    user: dict = Depends(require_org_access),
):
    item = await session.scalar(select(ActionItem).where(ActionItem.id == item_id, ActionItem.org_id == org_id))
    if not item:
        raise NotFoundError("ActionItem", str(item_id))

    if body.status is not None:
        item.status = body.status
    if body.assignee_id is not None:
        item.assignee_id = body.assignee_id
    if body.assignee_raw is not None:
        item.assignee_raw = body.assignee_raw
    if body.due_at is not None:
        item.due_at = body.due_at
    item.updated_at = datetime.now(timezone.utc)

    await session.flush()
    return ActionItemResponse.model_validate(item)
