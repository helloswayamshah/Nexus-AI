import json
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_async_session, require_org_access
from app.core.errors import NotFoundError
from app.models.enums import EventType, Platform
from app.models.event import Event, EventParticipant
from app.schemas.event import EventIngest, EventListResponse, EventResponse

router = APIRouter()


@router.post("", status_code=202)
async def ingest_event(
    org_id: UUID,
    body: EventIngest,
    session: AsyncSession = Depends(get_async_session),
    user: dict = Depends(require_org_access),
):
    event = Event(
        org_id=org_id,
        team_id=body.team_id,
        platform=body.platform,
        event_type=body.event_type,
        external_id=body.external_id,
        occurred_at=body.occurred_at,
        raw_content_json=json.dumps(body.raw_content) if body.raw_content else None,
    )
    session.add(event)
    await session.flush()

    for p in body.participants:
        session.add(EventParticipant(event_id=event.id, platform_id=p.platform_id, role=p.role))

    return {"event_id": str(event.id), "org_id": str(org_id), "status": "queued"}


@router.get("", response_model=EventListResponse)
async def list_events(
    org_id: UUID,
    event_type: Optional[EventType] = Query(default=None),
    platform: Optional[Platform] = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_async_session),
    user: dict = Depends(require_org_access),
):
    q = select(Event).where(Event.org_id == org_id)
    if event_type:
        q = q.where(Event.event_type == event_type)
    if platform:
        q = q.where(Event.platform == platform)

    total = await session.scalar(select(func.count()).select_from(q.subquery()))
    rows = (await session.scalars(q.order_by(Event.occurred_at.desc()).limit(limit).offset(offset))).all()

    items = [EventResponse.from_orm_with_content(r) for r in rows]
    return EventListResponse(items=items, total=total, limit=limit, offset=offset, has_more=(offset + limit) < total)


@router.get("/{event_id}", response_model=EventResponse)
async def get_event(
    org_id: UUID,
    event_id: UUID,
    session: AsyncSession = Depends(get_async_session),
    user: dict = Depends(require_org_access),
):
    event = await session.scalar(select(Event).where(Event.id == event_id, Event.org_id == org_id))
    if not event:
        raise NotFoundError("Event", str(event_id))
    return EventResponse.from_orm_with_content(event)
