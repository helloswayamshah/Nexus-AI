from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_async_session, require_org_access
from app.models.artifact import ActionItem
from app.models.enums import ActionItemStatus
from app.models.event import Event, EventParticipant
from app.schemas.insights import InsightsSummaryResponse

router = APIRouter()


@router.get("/summary", response_model=InsightsSummaryResponse)
async def insights_summary(
    org_id: UUID,
    period: str = Query(default="last_7_days"),
    session: AsyncSession = Depends(get_async_session),
    user: dict = Depends(require_org_access),
):
    total_events = await session.scalar(select(func.count(Event.id)).where(Event.org_id == org_id)) or 0
    total_items = await session.scalar(select(func.count(ActionItem.id)).where(ActionItem.org_id == org_id)) or 0
    open_items = await session.scalar(
        select(func.count(ActionItem.id)).where(
            ActionItem.org_id == org_id, ActionItem.status == ActionItemStatus.OPEN
        )
    ) or 0

    # distinct participants across all org events — rough proxy for active members
    active_members = await session.scalar(
        select(func.count(func.distinct(EventParticipant.platform_id))).where(
            EventParticipant.event_id.in_(select(Event.id).where(Event.org_id == org_id))
        )
    ) or 0

    return InsightsSummaryResponse(
        org_id=org_id,
        period=period,
        total_events=total_events,
        total_action_items=total_items,
        open_action_items=open_items,
        active_members=active_members,
        top_topics=[],  # Phase 4: populated from intelligence pipeline
    )
