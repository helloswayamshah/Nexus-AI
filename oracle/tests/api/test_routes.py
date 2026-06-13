"""
API integration tests — Phase 2 real routes.

All tests use a real SQLite DB (via conftest fixtures) with transaction rollback
isolation. No mocks — tests exercise the full request/response/DB stack.
"""

import pytest

# ── Helpers ───────────────────────────────────────────────────────────────

async def _register_and_login(client, email="user@example.com", password="pass1234", name="Test User"):
    await client.post("/auth/register", json={"email": email, "password": password, "display_name": name})
    r = await client.post("/auth/token", json={"email": email, "password": password})
    return r.json()["access_token"]


async def _auth_headers(client, email="user@example.com", password="pass1234", name="Test User"):
    token = await _register_and_login(client, email, password, name)
    return {"Authorization": f"Bearer {token}"}


async def _create_org(client, headers, name="Test Org"):
    r = await client.post("/orgs", json={"name": name}, headers=headers)
    return r.json()


# ── Auth ──────────────────────────────────────────────────────────────────

class TestAuth:
    async def test_register_returns_201(self, client):
        r = await client.post("/auth/register", json={"email": "reg1@example.com", "password": "pass1234", "display_name": "Reg One"})
        assert r.status_code == 201

    async def test_register_body_has_user_id(self, client):
        r = await client.post("/auth/register", json={"email": "reg2@example.com", "password": "pass1234", "display_name": "Reg Two"})
        assert "user_id" in r.json()

    async def test_register_duplicate_returns_409(self, client):
        await client.post("/auth/register", json={"email": "dup@example.com", "password": "pass1234", "display_name": "Dup"})
        r = await client.post("/auth/register", json={"email": "dup@example.com", "password": "pass1234", "display_name": "Dup"})
        assert r.status_code == 409

    async def test_token_returns_200(self, client):
        await client.post("/auth/register", json={"email": "tok1@example.com", "password": "pass1234", "display_name": "Tok"})
        r = await client.post("/auth/token", json={"email": "tok1@example.com", "password": "pass1234"})
        assert r.status_code == 200

    async def test_token_has_access_token(self, client):
        await client.post("/auth/register", json={"email": "tok2@example.com", "password": "pass1234", "display_name": "Tok"})
        r = await client.post("/auth/token", json={"email": "tok2@example.com", "password": "pass1234"})
        assert "access_token" in r.json()
        assert r.json()["token_type"] == "bearer"

    async def test_wrong_password_returns_401(self, client):
        await client.post("/auth/register", json={"email": "tok3@example.com", "password": "pass1234", "display_name": "Tok"})
        r = await client.post("/auth/token", json={"email": "tok3@example.com", "password": "wrongpass"})
        assert r.status_code == 401

    async def test_unknown_email_returns_401(self, client):
        r = await client.post("/auth/token", json={"email": "nobody@example.com", "password": "pass1234"})
        assert r.status_code == 401

    async def test_invalid_email_returns_422(self, client):
        r = await client.post("/auth/register", json={"email": "not-an-email", "password": "pass1234", "display_name": "Bad"})
        assert r.status_code == 422

    async def test_no_bearer_returns_401(self, client):
        r = await client.get("/orgs/00000000-0000-0000-0000-000000000001")
        assert r.status_code == 401


# ── Orgs ──────────────────────────────────────────────────────────────────

class TestOrgs:
    async def test_create_org_returns_201(self, client):
        h = await _auth_headers(client, "orgs1@example.com")
        r = await client.post("/orgs", json={"name": "My Org"}, headers=h)
        assert r.status_code == 201

    async def test_create_org_has_id_slug(self, client):
        h = await _auth_headers(client, "orgs2@example.com")
        r = await client.post("/orgs", json={"name": "Slug Org"}, headers=h)
        body = r.json()
        assert "id" in body
        assert body["slug"] == "slug-org"

    async def test_create_org_custom_slug(self, client):
        h = await _auth_headers(client, "orgs3@example.com")
        r = await client.post("/orgs", json={"name": "Any Name", "slug": "custom-slug"}, headers=h)
        assert r.json()["slug"] == "custom-slug"

    async def test_duplicate_slug_returns_409(self, client):
        h = await _auth_headers(client, "orgs4@example.com")
        await client.post("/orgs", json={"name": "Dupe Org", "slug": "dupe"}, headers=h)
        r = await client.post("/orgs", json={"name": "Dupe Org 2", "slug": "dupe"}, headers=h)
        assert r.status_code == 409

    async def test_get_org_returns_200(self, client):
        h = await _auth_headers(client, "orgs5@example.com")
        org = (await client.post("/orgs", json={"name": "Get Org"}, headers=h)).json()
        r = await client.get(f"/orgs/{org['id']}", headers=h)
        assert r.status_code == 200
        assert r.json()["id"] == org["id"]

    async def test_get_org_not_found_returns_404(self, client):
        h = await _auth_headers(client, "orgs6@example.com")
        r = await client.get("/orgs/00000000-0000-0000-0000-000000000099", headers=h)
        assert r.status_code == 404

    async def test_get_org_invalid_uuid_returns_422(self, client):
        h = await _auth_headers(client, "orgs7@example.com")
        r = await client.get("/orgs/not-a-uuid", headers=h)
        assert r.status_code == 422


# ── Events ────────────────────────────────────────────────────────────────

class TestEvents:
    async def _setup(self, client, tag: str):
        email = f"evts-{tag}@example.com"
        h = await _auth_headers(client, email)
        org = (await client.post("/orgs", json={"name": f"Events Org {tag}"}, headers=h)).json()
        return h, org["id"]

    async def test_ingest_returns_202(self, client):
        h, oid = await self._setup(client, "a1")
        r = await client.post(f"/orgs/{oid}/events", headers=h, json={
            "platform": "DISCORD", "event_type": "VOICE_CALL",
            "occurred_at": "2026-06-12T10:00:00Z"
        })
        assert r.status_code == 202

    async def test_ingest_has_event_id(self, client):
        h, oid = await self._setup(client, "a2")
        r = await client.post(f"/orgs/{oid}/events", headers=h, json={
            "platform": "DISCORD", "event_type": "VOICE_CALL",
            "occurred_at": "2026-06-12T10:00:00Z"
        })
        assert "event_id" in r.json()

    async def test_list_events_returns_200(self, client):
        h, oid = await self._setup(client, "a3")
        r = await client.get(f"/orgs/{oid}/events", headers=h)
        assert r.status_code == 200

    async def test_list_events_paginated(self, client):
        h, oid = await self._setup(client, "a4")
        for i in range(3):
            await client.post(f"/orgs/{oid}/events", headers=h, json={
                "platform": "SLACK", "event_type": "CHANNEL_DIGEST",
                "occurred_at": f"2026-06-{12+i}T10:00:00Z"
            })
        r = await client.get(f"/orgs/{oid}/events?limit=2&offset=0", headers=h)
        body = r.json()
        assert body["total"] == 3
        assert len(body["items"]) == 2
        assert body["has_more"] is True

    async def test_list_events_filter_by_type(self, client):
        h, oid = await self._setup(client, "a5")
        await client.post(f"/orgs/{oid}/events", headers=h, json={
            "platform": "DISCORD", "event_type": "VOICE_CALL", "occurred_at": "2026-06-12T10:00:00Z"
        })
        await client.post(f"/orgs/{oid}/events", headers=h, json={
            "platform": "SLACK", "event_type": "CHANNEL_DIGEST", "occurred_at": "2026-06-12T11:00:00Z"
        })
        r = await client.get(f"/orgs/{oid}/events?event_type=VOICE_CALL", headers=h)
        assert all(e["event_type"] == "VOICE_CALL" for e in r.json()["items"])

    async def test_get_event_returns_200(self, client):
        h, oid = await self._setup(client, "a6")
        ingest = (await client.post(f"/orgs/{oid}/events", headers=h, json={
            "platform": "DISCORD", "event_type": "VOICE_CALL", "occurred_at": "2026-06-12T10:00:00Z"
        })).json()
        r = await client.get(f"/orgs/{oid}/events/{ingest['event_id']}", headers=h)
        assert r.status_code == 200
        assert r.json()["id"] == ingest["event_id"]

    async def test_get_event_not_found_returns_404(self, client):
        h, oid = await self._setup(client, "a7")
        r = await client.get(f"/orgs/{oid}/events/00000000-0000-0000-0000-000000000099", headers=h)
        assert r.status_code == 404

    async def test_non_member_cannot_list_events_403(self, client):
        h, oid = await self._setup(client, "a8")
        h2 = await _auth_headers(client, "outsider@example.com")
        r = await client.get(f"/orgs/{oid}/events", headers=h2)
        assert r.status_code == 403


# ── Artifacts ─────────────────────────────────────────────────────────────

class TestArtifacts:
    async def test_list_artifacts_returns_200(self, client):
        h = await _auth_headers(client, "arts1@example.com")
        org = (await client.post("/orgs", json={"name": "Arts Org"}, headers=h)).json()
        r = await client.get(f"/orgs/{org['id']}/artifacts", headers=h)
        assert r.status_code == 200
        assert r.json()["total"] == 0
        assert isinstance(r.json()["items"], list)


# ── Action Items ──────────────────────────────────────────────────────────

class TestActionItems:
    async def test_list_action_items_returns_200(self, client):
        h = await _auth_headers(client, "aitems1@example.com")
        org = (await client.post("/orgs", json={"name": "Items Org"}, headers=h)).json()
        r = await client.get(f"/orgs/{org['id']}/action-items", headers=h)
        assert r.status_code == 200
        assert r.json()["total"] == 0


# ── Platform Links ────────────────────────────────────────────────────────

class TestPlatformLinks:
    async def _setup(self, client, tag: str):
        h = await _auth_headers(client, f"plat-{tag}@example.com")
        org = (await client.post("/orgs", json={"name": f"Plat Org {tag}"}, headers=h)).json()
        return h, org["id"]

    async def test_create_platform_link_returns_201(self, client):
        h, oid = await self._setup(client, "b1")
        r = await client.post(f"/orgs/{oid}/platform-links", headers=h, json={
            "platform": "SLACK", "external_id": "T123", "display_name": "My Slack"
        })
        assert r.status_code == 201

    async def test_create_platform_link_no_credentials_in_response(self, client):
        h, oid = await self._setup(client, "b2")
        r = await client.post(f"/orgs/{oid}/platform-links", headers=h, json={
            "platform": "DISCORD", "external_id": "G456",
            "credentials": {"bot_token": "xoxb-secret"}
        })
        assert "credentials" not in r.json()
        assert r.status_code == 201

    async def test_list_platform_links_returns_200(self, client):
        h, oid = await self._setup(client, "b3")
        await client.post(f"/orgs/{oid}/platform-links", headers=h, json={
            "platform": "SLACK", "external_id": "T999"
        })
        r = await client.get(f"/orgs/{oid}/platform-links", headers=h)
        assert r.status_code == 200
        assert r.json()["total"] >= 1


# ── Insights ──────────────────────────────────────────────────────────────

class TestInsights:
    async def test_insights_summary_returns_200(self, client):
        h = await _auth_headers(client, "ins1@example.com")
        org = (await client.post("/orgs", json={"name": "Ins Org"}, headers=h)).json()
        r = await client.get(f"/orgs/{org['id']}/insights/summary", headers=h)
        assert r.status_code == 200

    async def test_insights_summary_has_required_keys(self, client):
        h = await _auth_headers(client, "ins2@example.com")
        org = (await client.post("/orgs", json={"name": "Ins Org 2"}, headers=h)).json()
        r = await client.get(f"/orgs/{org['id']}/insights/summary", headers=h)
        body = r.json()
        for key in ("org_id", "period", "total_events", "total_action_items", "open_action_items", "active_members", "top_topics"):
            assert key in body

    async def test_insights_counts_real_data(self, client):
        h = await _auth_headers(client, "ins3@example.com")
        org = (await client.post("/orgs", json={"name": "Ins Org 3"}, headers=h)).json()
        oid = org["id"]
        await client.post(f"/orgs/{oid}/events", headers=h, json={
            "platform": "DISCORD", "event_type": "VOICE_CALL",
            "occurred_at": "2026-06-12T10:00:00Z",
            "participants": [{"platform_id": "u1", "role": "host"}]
        })
        r = await client.get(f"/orgs/{oid}/insights/summary", headers=h)
        body = r.json()
        assert body["total_events"] == 1
        assert body["active_members"] == 1


# ── Error format ──────────────────────────────────────────────────────────

class TestErrorFormat:
    async def test_404_has_error_wrapper(self, client):
        r = await client.get("/orgs/00000000-0000-0000-0000-000000000001/events/00000000-0000-0000-0000-000000000099")
        # 401 because no auth, but error shape is what we care about
        assert "error" in r.json()

    async def test_422_has_error_wrapper_with_details(self, client):
        r = await client.post("/auth/register", json={"email": "bad", "password": "x", "display_name": "Y"})
        body = r.json()
        assert r.status_code == 422
        assert body["error"]["code"] == "VALIDATION_ERROR"
        assert isinstance(body["error"]["details"], list)
