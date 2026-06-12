"""
End-to-end Phase 0+1 verification script.
Run: uv run python verify_phase01.py
"""
import asyncio
import os
import uuid

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./verify_test.db")

PASS = []
FAIL = []

def ok(msg): PASS.append(msg); print(f"  PASS  {msg}")
def fail(msg, err): FAIL.append(msg); print(f"  FAIL  {msg}: {err}")


# ── 1. All models import ──────────────────────────────────────────────────
try:
    from app.models import Base
    from app.models.org import Org
    from app.models.user import User
    from app.models.team import Team
    from app.models.platform import OrgMember, TeamMember, PlatformLink, PlatformIdentity
    from app.models.event import Event, EventParticipant
    from app.models.artifact import Artifact, ActionItem
    from app.models.enums import Platform, EventType, ArtifactType, ActionItemStatus, OrgRole, TeamRole
    ok("All 11 models import without error")
except Exception as e:
    fail("Model imports", e)


# ── 2. Base.metadata has all 11 tables ───────────────────────────────────
try:
    table_names = set(Base.metadata.tables.keys())
    expected = {"orgs","users","teams","org_members","team_members","platform_links",
                "platform_identities","events","event_participants","artifacts","action_items"}
    missing = expected - table_names
    assert not missing, f"Missing from metadata: {missing}"
    ok(f"Base.metadata contains all 11 tables")
except Exception as e:
    fail("Base.metadata completeness", e)


# ── 3. OrgScopedRepository isolation invariant ───────────────────────────
async def test_repo():
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    from app.repositories.org_repo import OrgRepository
    from app.repositories.event_repo import EventRepository

    engine = create_async_engine("sqlite+aiosqlite:///./verify_test.db")
    Session = async_sessionmaker(engine, expire_on_commit=False)

    async with Session() as s:
        repo = OrgRepository(s)

        # Create an org
        org = await repo.create(Org(slug=f"test-{uuid.uuid4().hex[:6]}", display_name="Test Org"))
        await s.commit()
        ok(f"OrgRepository.create - org_id={org.id}")

        # Fetch it back by id
        found = await repo.get_by_id(org.id)
        assert found is not None and found.slug == org.slug
        ok("OrgRepository.get_by_id - returns correct record")

        # Fetch by slug
        found_slug = await repo.get_by_slug(org.slug)
        assert found_slug is not None and found_slug.id == org.id
        ok("OrgRepository.get_by_slug - returns correct record")

        # Non-existent id returns None (not exception)
        missing = await repo.get_by_id(uuid.uuid4())
        assert missing is None
        ok("OrgRepository.get_by_id - unknown id returns None")

        # OrgScopedRepository cross-org isolation
        org_b = await repo.create(Org(slug=f"other-{uuid.uuid4().hex[:6]}", display_name="Other Org"))
        await s.commit()

        event_repo_a = EventRepository(s, org.id)
        event_repo_b = EventRepository(s, org_b.id)

        from datetime import datetime
        event = Event(
            org_id=org.id,
            platform=Platform.DISCORD,
            event_type=EventType.VOICE_CALL,
            occurred_at=datetime.utcnow(),
            created_at=datetime.utcnow(),
        )
        s.add(event)
        await s.flush()
        await s.commit()

        # repo_a can see event
        events_a = await event_repo_a.list_all()
        assert any(e.id == event.id for e in events_a)
        ok("OrgScopedRepository - org_a sees its own event")

        # repo_b cannot see org_a's event
        events_b = await event_repo_b.list_all()
        assert not any(e.id == event.id for e in events_b)
        ok("OrgScopedRepository - org_b cannot see org_a's event (isolation holds)")

    await engine.dispose()

try:
    asyncio.run(test_repo())
except Exception as e:
    fail("Repository tests", e)


# ── 4. Crypto vault - round-trip + wire format ───────────────────────────
try:
    os.environ["ENCRYPTION_KEY"] = "a" * 64  # 64 hex chars = 32 bytes

    from app.core.crypto import encrypt, decrypt, is_encrypted

    plaintext = "super-secret-bot-token"
    encrypted = encrypt(plaintext)

    parts = encrypted.split(":")
    assert parts[0] == "v1", f"Wrong version prefix: {parts[0]}"
    assert len(parts) == 4, f"Expected 4 colon parts, got {len(parts)}"
    ok("Crypto format v1:<iv>:<tag>:<ct> - OK")

    recovered = decrypt(encrypted)
    assert recovered == plaintext
    ok("Crypto round-trip encrypt->decrypt")

    assert is_encrypted(encrypted)
    assert not is_encrypted("raw-plaintext")
    ok("is_encrypted guard works")

    # Two encryptions of same plaintext produce different ciphertext (random IV)
    enc2 = encrypt(plaintext)
    assert enc2 != encrypted
    ok("Crypto uses fresh random IV per call (no deterministic leak)")

except Exception as e:
    fail("Crypto vault", e)


# ── 5. Config reads DATABASE_URL ─────────────────────────────────────────
try:
    from app.config import get_settings
    settings = get_settings()
    assert "sqlite" in settings.database_url or "postgresql" in settings.database_url
    ok(f"Config loaded - DATABASE_URL driver: {settings.database_url.split('+')[0]}")
except Exception as e:
    fail("Config", e)


# ── Summary ───────────────────────────────────────────────────────────────
print()
print(f"{'='*50}")
print(f"  {len(PASS)} passed  |  {len(FAIL)} failed")
if FAIL:
    print("  Failed checks:")
    for f in FAIL:
        print(f"    - {f}")
print(f"{'='*50}")
