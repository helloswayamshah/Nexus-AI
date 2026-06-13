from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict
import json

from app.models.enums import ArtifactType


class ArtifactResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    org_id: UUID
    event_id: Optional[UUID]
    artifact_type: ArtifactType
    content: str
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime

    @classmethod
    def from_orm_with_meta(cls, obj) -> "ArtifactResponse":
        data = {c.key: getattr(obj, c.key) for c in obj.__table__.columns}
        raw = data.pop("metadata_json", None)
        data["metadata"] = json.loads(raw) if raw else None
        return cls(**data)


class ArtifactListResponse(BaseModel):
    items: List[ArtifactResponse]
    total: int
    limit: int
    offset: int
    has_more: bool
