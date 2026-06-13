from typing import List
from uuid import UUID

from pydantic import BaseModel


class InsightsSummaryResponse(BaseModel):
    org_id: UUID
    period: str
    total_events: int
    total_action_items: int
    open_action_items: int
    active_members: int
    top_topics: List[str]
