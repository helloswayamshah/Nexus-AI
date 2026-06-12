import enum


class Platform(str, enum.Enum):
    DISCORD = "DISCORD"
    SLACK = "SLACK"
    ZOOM = "ZOOM"
    TEAMS = "TEAMS"


class EventType(str, enum.Enum):
    VOICE_CALL = "VOICE_CALL"
    CHANNEL_DIGEST = "CHANNEL_DIGEST"
    FILE_UPLOAD = "FILE_UPLOAD"
    WEBHOOK = "WEBHOOK"


class ArtifactType(str, enum.Enum):
    TRANSCRIPT = "TRANSCRIPT"
    SUMMARY = "SUMMARY"
    ACTION_ITEMS = "ACTION_ITEMS"
    INSIGHT = "INSIGHT"
    ANOMALY_REPORT = "ANOMALY_REPORT"
    WEEKLY_DIGEST = "WEEKLY_DIGEST"


class ActionItemStatus(str, enum.Enum):
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    DONE = "DONE"
    CANCELLED = "CANCELLED"


class OrgRole(str, enum.Enum):
    OWNER = "OWNER"
    ADMIN = "ADMIN"
    MEMBER = "MEMBER"


class TeamRole(str, enum.Enum):
    LEAD = "LEAD"
    MEMBER = "MEMBER"
