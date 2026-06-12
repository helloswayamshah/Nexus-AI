import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, UUIDMixin
from app.models.enums import EventType, Platform


class Event(Base, UUIDMixin):
    __tablename__ = "events"
    __table_args__ = (
        UniqueConstraint("org_id", "platform", "external_id", name="uq_event_org_plat_ext"),
        Index("ix_event_org_occurred", "org_id", "occurred_at"),
        Index("ix_event_org_type", "org_id", "event_type"),
    )

    org_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("orgs.id", ondelete="CASCADE"), nullable=False)
    team_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("teams.id", ondelete="SET NULL"), nullable=True)
    platform: Mapped[Platform] = mapped_column(SAEnum(Platform, native_enum=False, length=16), nullable=False)
    event_type: Mapped[EventType] = mapped_column(SAEnum(EventType, native_enum=False, length=32), nullable=False)
    external_id: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    raw_content_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class EventParticipant(Base):
    __tablename__ = "event_participants"

    event_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("events.id", ondelete="CASCADE"), primary_key=True)
    platform_id: Mapped[str] = mapped_column(String(256), primary_key=True)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    role: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
