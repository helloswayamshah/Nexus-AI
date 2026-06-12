from app.models.base import Base  # noqa: F401

# Import all models so Base.metadata is fully populated for Alembic
from app.models.org import Org  # noqa: F401
from app.models.user import User  # noqa: F401
from app.models.team import Team  # noqa: F401
from app.models.platform import OrgMember, TeamMember, PlatformLink, PlatformIdentity  # noqa: F401
from app.models.event import Event, EventParticipant  # noqa: F401
from app.models.artifact import Artifact, ActionItem  # noqa: F401
