"""
API tests — all stub routes.

Verifies every router is mounted, returns the correct HTTP status code,
the response is valid JSON, and the expected top-level keys are present.
These tests will be replaced/extended in Phase 2 when routes return real data.
"""

import pytest

ORG = "00000000-0000-0000-0000-000000000001"
EVENT = "00000000-0000-0000-0000-000000000002"
ITEM = "00000000-0000-0000-0000-000000000003"


# ── Auth ──────────────────────────────────────────────────────────────────

class TestAuth:
    async def test_token_returns_200(self, client):
        r = await client.post("/auth/token")
        assert r.status_code == 200

    async def test_token_body_has_access_token(self, client):
        r = await client.post("/auth/token")
        assert "access_token" in r.json()

    async def test_token_body_has_token_type(self, client):
        r = await client.post("/auth/token")
        assert r.json()["token_type"] == "bearer"


# ── Orgs ──────────────────────────────────────────────────────────────────

class TestOrgs:
    async def test_create_org_returns_201(self, client):
        r = await client.post("/orgs", json={})
        assert r.status_code == 201

    async def test_create_org_body_has_message(self, client):
        r = await client.post("/orgs", json={})
        assert "message" in r.json()

    async def test_get_org_returns_200(self, client):
        r = await client.get(f"/orgs/{ORG}")
        assert r.status_code == 200

    async def test_get_org_echoes_org_id(self, client):
        r = await client.get(f"/orgs/{ORG}")
        assert r.json()["org_id"] == ORG

    async def test_get_org_invalid_uuid_returns_422(self, client):
        r = await client.get("/orgs/not-a-uuid")
        assert r.status_code == 422

    async def test_get_org_422_body_has_detail(self, client):
        r = await client.get("/orgs/not-a-uuid")
        assert "detail" in r.json()


# ── Events ────────────────────────────────────────────────────────────────

class TestEvents:
    async def test_ingest_event_returns_202(self, client):
        r = await client.post(f"/orgs/{ORG}/events", json={})
        assert r.status_code == 202

    async def test_ingest_event_body_has_org_id(self, client):
        r = await client.post(f"/orgs/{ORG}/events", json={})
        assert r.json()["org_id"] == ORG

    async def test_list_events_returns_200(self, client):
        r = await client.get(f"/orgs/{ORG}/events")
        assert r.status_code == 200

    async def test_list_events_body_has_events_key(self, client):
        r = await client.get(f"/orgs/{ORG}/events")
        assert "events" in r.json()

    async def test_list_events_events_is_list(self, client):
        r = await client.get(f"/orgs/{ORG}/events")
        assert isinstance(r.json()["events"], list)

    async def test_get_event_returns_200(self, client):
        r = await client.get(f"/orgs/{ORG}/events/{EVENT}")
        assert r.status_code == 200

    async def test_get_event_echoes_event_id(self, client):
        r = await client.get(f"/orgs/{ORG}/events/{EVENT}")
        assert r.json()["event_id"] == EVENT

    async def test_invalid_event_uuid_returns_422(self, client):
        r = await client.get(f"/orgs/{ORG}/events/bad-uuid")
        assert r.status_code == 422


# ── Artifacts ─────────────────────────────────────────────────────────────

class TestArtifacts:
    async def test_list_artifacts_returns_200(self, client):
        r = await client.get(f"/orgs/{ORG}/artifacts")
        assert r.status_code == 200

    async def test_list_artifacts_has_artifacts_key(self, client):
        r = await client.get(f"/orgs/{ORG}/artifacts")
        assert "artifacts" in r.json()

    async def test_list_artifacts_is_list(self, client):
        r = await client.get(f"/orgs/{ORG}/artifacts")
        assert isinstance(r.json()["artifacts"], list)


# ── Action Items ──────────────────────────────────────────────────────────

class TestActionItems:
    async def test_list_action_items_returns_200(self, client):
        r = await client.get(f"/orgs/{ORG}/action-items")
        assert r.status_code == 200

    async def test_list_action_items_has_items_key(self, client):
        r = await client.get(f"/orgs/{ORG}/action-items")
        assert "items" in r.json()

    async def test_list_action_items_is_list(self, client):
        r = await client.get(f"/orgs/{ORG}/action-items")
        assert isinstance(r.json()["items"], list)

    async def test_patch_action_item_returns_200(self, client):
        r = await client.patch(f"/orgs/{ORG}/action-items/{ITEM}", json={})
        assert r.status_code == 200

    async def test_patch_action_item_echoes_item_id(self, client):
        r = await client.patch(f"/orgs/{ORG}/action-items/{ITEM}", json={})
        assert r.json()["item_id"] == ITEM


# ── Platform Links ────────────────────────────────────────────────────────

class TestPlatformLinks:
    async def test_create_platform_link_returns_201(self, client):
        r = await client.post(f"/orgs/{ORG}/platform-links", json={})
        assert r.status_code == 201

    async def test_create_platform_link_has_message(self, client):
        r = await client.post(f"/orgs/{ORG}/platform-links", json={})
        assert "message" in r.json()

    async def test_list_platform_links_returns_200(self, client):
        r = await client.get(f"/orgs/{ORG}/platform-links")
        assert r.status_code == 200

    async def test_list_platform_links_has_links_key(self, client):
        r = await client.get(f"/orgs/{ORG}/platform-links")
        assert "links" in r.json()

    async def test_list_platform_links_is_list(self, client):
        r = await client.get(f"/orgs/{ORG}/platform-links")
        assert isinstance(r.json()["links"], list)


# ── Insights ──────────────────────────────────────────────────────────────

class TestInsights:
    async def test_insights_summary_returns_200(self, client):
        r = await client.get(f"/orgs/{ORG}/insights/summary")
        assert r.status_code == 200

    async def test_insights_summary_has_required_keys(self, client):
        r = await client.get(f"/orgs/{ORG}/insights/summary")
        body = r.json()
        for key in ("org_id", "period", "total_events", "total_action_items",
                    "open_action_items", "active_members", "top_topics"):
            assert key in body, f"Missing key: {key}"

    async def test_insights_summary_counts_are_zero(self, client):
        r = await client.get(f"/orgs/{ORG}/insights/summary")
        body = r.json()
        assert body["total_events"] == 0
        assert body["total_action_items"] == 0
        assert body["open_action_items"] == 0

    async def test_insights_summary_echoes_org_id(self, client):
        r = await client.get(f"/orgs/{ORG}/insights/summary")
        assert r.json()["org_id"] == ORG
