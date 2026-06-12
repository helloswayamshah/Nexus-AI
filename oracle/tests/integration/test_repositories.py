"""
Integration tests for all repositories.

Uses the db_session fixture from conftest — each test runs inside a
transaction that is rolled back after, so tests are fully isolated
without recreating the schema.
"""

import uuid
from datetime import datetime, timezone

import pytest

from app.models.artifact import ActionItem, Artifact
from app.models.enums import (
    ActionItemStatus,
    ArtifactType,
    EventType,
    OrgRole,
    Platform,
    TeamRole,
)
from app.models.event import Event, EventParticipant
from app.models.org import Org
from app.models.platform import OrgMember, PlatformIdentity, PlatformLink
from app.models.team import Team
from app.models.user import User
from app.repositories.action_item_repo import ActionItemRepository
from app.repositories.artifact_repo import ArtifactRepository
from app.repositories.event_repo import EventRepository
from app.repositories.org_repo import OrgRepository
from app.repositories.user_repo import UserRepository


# ── Helpers ───────────────────────────────────────────────────────────────

def now():
    return datetime.now(timezone.utc)


async def make_org(session, slug=None) -> Org:
    repo = OrgRepository(session)
    org = await repo.create(Org(slug=slug or f"org-{uuid.uuid4().hex[:6]}", display_name="Test Org"))
    await session.flush()
    return org


async def make_user(session, email=None) -> User:
    repo = UserRepository(session)
    user = await repo.create(User(email=email or f"user-{uuid.uuid4().hex[:6]}@test.com", name="Test User", created_at=now()))
    await session.flush()
    return user


async def make_event(session, org_id) -> Event:
    event = Event(
        org_id=org_id,
        platform=Platform.DISCORD,
        event_type=EventType.VOICE_CALL,
        occurred_at=now(),
        created_at=now(),
    )
    session.add(event)
    await session.flush()
    return event


async def make_artifact(session, org_id, event_id=None) -> Artifact:
    repo = ArtifactRepository(session, org_id)
    artifact = await repo.create(Artifact(
        event_id=event_id,
        artifact_type=ArtifactType.SUMMARY,
        content="Test summary content",
        created_at=now(),
    ))
    await session.flush()
    return artifact


# ── OrgRepository ─────────────────────────────────────────────────────────

class TestOrgRepository:
    async def test_create_and_get_by_id(self, db_session):
        repo = OrgRepository(db_session)
        org = await repo.create(Org(slug="create-test", display_name="Create Test"))
        await db_session.flush()
        found = await repo.get_by_id(org.id)
        assert found is not None
        assert found.slug == "create-test"

    async def test_get_by_id_unknown_returns_none(self, db_session):
        repo = OrgRepository(db_session)
        assert await repo.get_by_id(uuid.uuid4()) is None

    async def test_get_by_slug(self, db_session):
        repo = OrgRepository(db_session)
        await repo.create(Org(slug="slug-lookup", display_name="Slug Lookup"))
        await db_session.flush()
        found = await repo.get_by_slug("slug-lookup")
        assert found is not None
        assert found.slug == "slug-lookup"

    async def test_get_by_slug_unknown_returns_none(self, db_session):
        repo = OrgRepository(db_session)
        assert await repo.get_by_slug("does-not-exist") is None


# ── UserRepository ────────────────────────────────────────────────────────

class TestUserRepository:
    async def test_create_and_get_by_id(self, db_session):
        repo = UserRepository(db_session)
        user = await repo.create(User(email="u1@test.com", name="User One", created_at=now()))
        await db_session.flush()
        found = await repo.get_by_id(user.id)
        assert found.email == "u1@test.com"

    async def test_get_by_email(self, db_session):
        repo = UserRepository(db_session)
        await repo.create(User(email="lookup@test.com", name="Lookup", created_at=now()))
        await db_session.flush()
        found = await repo.get_by_email("lookup@test.com")
        assert found is not None

    async def test_get_by_email_unknown_returns_none(self, db_session):
        repo = UserRepository(db_session)
        assert await repo.get_by_email("nobody@test.com") is None


# ── OrgScopedRepository isolation ────────────────────────────────────────

class TestOrgIsolation:
    async def test_event_scoped_to_org(self, db_session):
        org_a = await make_org(db_session)
        org_b = await make_org(db_session)
        event = await make_event(db_session, org_a.id)

        repo_a = EventRepository(db_session, org_a.id)
        repo_b = EventRepository(db_session, org_b.id)

        events_a = await repo_a.list_all()
        events_b = await repo_b.list_all()

        assert any(e.id == event.id for e in events_a)
        assert not any(e.id == event.id for e in events_b)

    async def test_artifact_scoped_to_org(self, db_session):
        org_a = await make_org(db_session)
        org_b = await make_org(db_session)
        artifact = await make_artifact(db_session, org_a.id)

        repo_a = ArtifactRepository(db_session, org_a.id)
        repo_b = ArtifactRepository(db_session, org_b.id)

        arts_a = await repo_a.list_all()
        arts_b = await repo_b.list_all()

        assert any(a.id == artifact.id for a in arts_a)
        assert not any(a.id == artifact.id for a in arts_b)

    async def test_get_by_id_wrong_org_returns_none(self, db_session):
        org_a = await make_org(db_session)
        org_b = await make_org(db_session)
        event = await make_event(db_session, org_a.id)

        repo_b = EventRepository(db_session, org_b.id)
        assert await repo_b.get_by_id(event.id) is None

    async def test_create_forces_org_id(self, db_session):
        org = await make_org(db_session)
        repo = ArtifactRepository(db_session, org.id)
        artifact = await repo.create(Artifact(
            artifact_type=ArtifactType.TRANSCRIPT,
            content="forced org_id test",
            created_at=now(),
        ))
        await db_session.flush()
        assert artifact.org_id == org.id

    async def test_delete_wrong_org_raises(self, db_session):
        org_a = await make_org(db_session)
        org_b = await make_org(db_session)
        artifact = await make_artifact(db_session, org_a.id)

        repo_b = ArtifactRepository(db_session, org_b.id)
        with pytest.raises(ValueError, match="different org"):
            await repo_b.delete(artifact)


# ── EventRepository ───────────────────────────────────────────────────────

class TestEventRepository:
    async def test_list_filtered_by_platform(self, db_session):
        org = await make_org(db_session)
        discord_event = Event(org_id=org.id, platform=Platform.DISCORD,
                              event_type=EventType.VOICE_CALL, occurred_at=now(), created_at=now())
        slack_event = Event(org_id=org.id, platform=Platform.SLACK,
                            event_type=EventType.CHANNEL_DIGEST, occurred_at=now(), created_at=now())
        db_session.add_all([discord_event, slack_event])
        await db_session.flush()

        repo = EventRepository(db_session, org.id)
        discord_only = await repo.list_filtered(platform=Platform.DISCORD)
        assert all(e.platform == Platform.DISCORD for e in discord_only)

    async def test_list_filtered_by_event_type(self, db_session):
        org = await make_org(db_session)
        db_session.add(Event(org_id=org.id, platform=Platform.DISCORD,
                             event_type=EventType.VOICE_CALL, occurred_at=now(), created_at=now()))
        db_session.add(Event(org_id=org.id, platform=Platform.SLACK,
                             event_type=EventType.CHANNEL_DIGEST, occurred_at=now(), created_at=now()))
        await db_session.flush()

        repo = EventRepository(db_session, org.id)
        calls = await repo.list_filtered(event_type=EventType.VOICE_CALL)
        assert all(e.event_type == EventType.VOICE_CALL for e in calls)

    async def test_get_by_external_id(self, db_session):
        org = await make_org(db_session)
        event = Event(org_id=org.id, platform=Platform.DISCORD, event_type=EventType.VOICE_CALL,
                      external_id="ext-123", occurred_at=now(), created_at=now())
        db_session.add(event)
        await db_session.flush()

        repo = EventRepository(db_session, org.id)
        found = await repo.get_by_external_id(Platform.DISCORD, "ext-123")
        assert found is not None and found.id == event.id

    async def test_get_by_external_id_wrong_platform_returns_none(self, db_session):
        org = await make_org(db_session)
        db_session.add(Event(org_id=org.id, platform=Platform.DISCORD, event_type=EventType.VOICE_CALL,
                             external_id="ext-456", occurred_at=now(), created_at=now()))
        await db_session.flush()

        repo = EventRepository(db_session, org.id)
        assert await repo.get_by_external_id(Platform.SLACK, "ext-456") is None


# ── ArtifactRepository ────────────────────────────────────────────────────

class TestArtifactRepository:
    async def test_list_by_event(self, db_session):
        org = await make_org(db_session)
        event = await make_event(db_session, org.id)
        a1 = await make_artifact(db_session, org.id, event.id)
        a2 = await make_artifact(db_session, org.id, event.id)
        orphan = await make_artifact(db_session, org.id)  # no event

        repo = ArtifactRepository(db_session, org.id)
        by_event = await repo.list_by_event(event.id)
        ids = [a.id for a in by_event]
        assert a1.id in ids
        assert a2.id in ids
        assert orphan.id not in ids

    async def test_list_by_type(self, db_session):
        org = await make_org(db_session)
        repo = ArtifactRepository(db_session, org.id)
        await repo.create(Artifact(artifact_type=ArtifactType.SUMMARY, content="s", created_at=now()))
        await repo.create(Artifact(artifact_type=ArtifactType.TRANSCRIPT, content="t", created_at=now()))
        await db_session.flush()

        summaries = await repo.list_by_type(ArtifactType.SUMMARY)
        assert all(a.artifact_type == ArtifactType.SUMMARY for a in summaries)


# ── ActionItemRepository ──────────────────────────────────────────────────

class TestActionItemRepository:
    async def _make_action_item(self, session, org_id, artifact_id, status=ActionItemStatus.OPEN) -> ActionItem:
        repo = ActionItemRepository(session, org_id)
        item = await repo.create(ActionItem(
            artifact_id=artifact_id,
            text="Do something",
            status=status,
            created_at=now(),
            updated_at=now(),
        ))
        await session.flush()
        return item

    async def test_list_filtered_by_status(self, db_session):
        org = await make_org(db_session)
        artifact = await make_artifact(db_session, org.id)
        await self._make_action_item(db_session, org.id, artifact.id, ActionItemStatus.OPEN)
        await self._make_action_item(db_session, org.id, artifact.id, ActionItemStatus.DONE)

        repo = ActionItemRepository(db_session, org.id)
        open_items = await repo.list_filtered(status=ActionItemStatus.OPEN)
        assert all(i.status == ActionItemStatus.OPEN for i in open_items)

    async def test_update_status(self, db_session):
        org = await make_org(db_session)
        artifact = await make_artifact(db_session, org.id)
        item = await self._make_action_item(db_session, org.id, artifact.id)

        repo = ActionItemRepository(db_session, org.id)
        updated = await repo.update_status(item.id, ActionItemStatus.DONE)
        assert updated.status == ActionItemStatus.DONE

    async def test_update_status_unknown_id_returns_none(self, db_session):
        org = await make_org(db_session)
        repo = ActionItemRepository(db_session, org.id)
        result = await repo.update_status(uuid.uuid4(), ActionItemStatus.DONE)
        assert result is None
