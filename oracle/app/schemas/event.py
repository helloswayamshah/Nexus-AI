from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator
import json

from app.models.enums import EventType, Platform


class EventParticipantIn(BaseModel):
    platform_id: str
    role: Optional[str] = None


class EventIngest(BaseModel):
    platform: Platform
    event_type: EventType
    external_id: Optional[str] = None
    occurred_at: datetime
    team_id: Optional[UUID] = None
    participants: List[EventParticipantIn] = []
    raw_content: Optional[Dict[str, Any]] = None


class EventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    org_id: UUID
    team_id: Optional[UUID]
    platform: Platform
    event_type: EventType
    external_id: Optional[str]
    occurred_at: datetime
    created_at: datetime
    raw_content: Optional[Dict[str, Any]] = None

    @classmethod
    def from_orm_with_content(cls, obj) -> "EventResponse":
        data = {c.key: getattr(obj, c.key) for c in obj.__table__.columns}
        raw = data.pop("raw_content_json", None)
        data["raw_content"] = json.loads(raw) if raw else None
        return cls(**data)


class EventListResponse(BaseModel):
    items: List[EventResponse]
    total: int
    limit: int
    offset: int
    has_more: bool
