from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.enums import ActionItemStatus


class ActionItemUpdate(BaseModel):
    status: Optional[ActionItemStatus] = None
    assignee_id: Optional[UUID] = None
    assignee_raw: Optional[str] = None
    due_at: Optional[datetime] = None


class ActionItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    org_id: UUID
    artifact_id: UUID
    assignee_id: Optional[UUID]
    assignee_raw: Optional[str]
    text: str
    status: ActionItemStatus
    due_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime


class ActionItemListResponse(BaseModel):
    items: List[ActionItemResponse]
    total: int
    limit: int
    offset: int
    has_more: bool
