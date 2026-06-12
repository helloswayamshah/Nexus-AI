"""
API tests — health, OpenAPI schema, and 404 behaviour.
"""

import pytest


class TestHealth:
    async def test_health_returns_200(self, client):
        r = await client.get("/health")
        assert r.status_code == 200

    async def test_health_body(self, client):
        r = await client.get("/health")
        body = r.json()
        assert body["status"] == "ok"
        assert body["service"] == "nexus-oracle"


class TestOpenAPI:
    async def test_openapi_json_returns_200(self, client):
        r = await client.get("/openapi.json")
        assert r.status_code == 200

    async def test_openapi_has_correct_title(self, client):
        r = await client.get("/openapi.json")
        assert r.json()["info"]["title"] == "Nexus Oracle"

    async def test_openapi_exposes_all_route_groups(self, client):
        r = await client.get("/openapi.json")
        tags = {tag["name"] for tag in r.json().get("tags", [])}
        # FastAPI also populates tags from route definitions — check paths
        paths = r.json()["paths"]
        path_str = " ".join(paths.keys())
        assert "/health" in path_str
        assert "/orgs" in path_str
        assert "/auth/token" in path_str

    async def test_docs_ui_returns_200(self, client):
        r = await client.get("/docs")
        assert r.status_code == 200


class TestNotFound:
    async def test_unknown_root_path_returns_404(self, client):
        r = await client.get("/does-not-exist")
        assert r.status_code == 404

    async def test_unknown_nested_path_returns_404(self, client):
        ORG = "00000000-0000-0000-0000-000000000001"
        r = await client.get(f"/orgs/{ORG}/does-not-exist")
        assert r.status_code == 404
