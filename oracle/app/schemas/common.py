from typing import Generic, List, Optional, TypeVar
from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class ErrorDetail(BaseModel):
    field: Optional[str] = None
    message: str


class ErrorBody(BaseModel):
    code: str
    message: str
    details: List[ErrorDetail] = []


class ErrorResponse(BaseModel):
    error: ErrorBody


class CursorPage(BaseModel, Generic[T]):
    model_config = ConfigDict(from_attributes=True)

    items: List[T]
    total: int
    limit: int
    offset: int
    has_more: bool
