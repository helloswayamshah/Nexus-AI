from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.enums import Platform


class PlatformLinkCreate(BaseModel):
    platform: Platform
    external_id: str
    display_name: Optional[str] = None
    credentials: Optional[Dict[str, Any]] = None
    config: Optional[Dict[str, Any]] = None


class PlatformLinkResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    org_id: UUID
    platform: Platform
    external_id: str
    display_name: Optional[str]
    # credentials intentionally omitted — never returned
    created_at: datetime
    updated_at: datetime


class PlatformLinkListResponse(BaseModel):
    items: List[PlatformLinkResponse]
    total: int
