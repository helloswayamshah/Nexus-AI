from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict


class OrgCreate(BaseModel):
    name: str
    slug: Optional[str] = None


class OrgResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    slug: str
    created_at: datetime
