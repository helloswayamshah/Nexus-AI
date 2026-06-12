import uuid
from typing import Optional

from sqlalchemy import Enum as SAEnum, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, UUIDMixin, TimestampMixin
from app.models.enums import OrgRole, Platform, TeamRole


class OrgMember(Base):
    __tablename__ = "org_members"

    org_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("orgs.id", ondelete="CASCADE"), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    role: Mapped[OrgRole] = mapped_column(SAEnum(OrgRole, native_enum=False, length=16), nullable=False)


class TeamMember(Base):
    __tablename__ = "team_members"

    team_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("teams.id", ondelete="CASCADE"), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    role: Mapped[TeamRole] = mapped_column(SAEnum(TeamRole, native_enum=False, length=16), nullable=False)


class PlatformLink(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "platform_links"
    __table_args__ = (UniqueConstraint("org_id", "platform", "external_id", name="uq_platform_link_org_plat_ext"),)

    org_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("orgs.id", ondelete="CASCADE"), index=True, nullable=False)
    platform: Mapped[Platform] = mapped_column(SAEnum(Platform, native_enum=False, length=16), nullable=False)
    external_id: Mapped[str] = mapped_column(String(256), nullable=False)
    display_name: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    credentials_encrypted: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    config_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class PlatformIdentity(Base):
    __tablename__ = "platform_identities"

    platform: Mapped[Platform] = mapped_column(SAEnum(Platform, native_enum=False, length=16), primary_key=True)
    external_id: Mapped[str] = mapped_column(String(256), primary_key=True)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True
    )
