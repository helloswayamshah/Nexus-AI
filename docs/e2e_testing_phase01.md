# E2E Testing Guide — Phase 0+1

This guide covers every observable behaviour of the oracle as it stands today.
All routes are stubs returning Phase 2 placeholders — the tests here confirm
the server, routing, dependency injection, session lifecycle, and database
layer all work correctly end-to-end before Phase 2 builds on top.

---

## Prerequisites

```powershell
# From repo root — starts postgres in Docker, oracle on host with hot-reload
make dev-sqlite   # zero Docker, SQLite only (fastest)
# OR
make dev          # postgres in Docker + oracle on host
```

Oracle must be running at `http://localhost:8000` before running any HTTP steps.

---

## 1. Health & Boot

### 1.1 Health endpoint responds
```powershell
curl http://localhost:8000/health
```
**Expected:**
```json
{"status": "ok", "service": "nexus-oracle"}
```
**What it proves:** FastAPI app factory ran, lifespan handler completed,
database engine initialized without error.

### 1.2 OpenAPI schema generates
```powershell
curl http://localhost:8000/openapi.json | python -m json.tool | findstr '"title"'
```
**Expected:** `"title": "Nexus Oracle"`

Open `http://localhost:8000/docs` in a browser and confirm these 8 tag groups
appear in the sidebar:
- Auth
- Orgs
- Events
- Artifacts
- Action Items
- Platform Links
- Insights
- System

**What it proves:** All 8 routers are mounted, no import errors in any route file.

---

## 2. Auth

### 2.1 Token endpoint returns stub token
```powershell
curl -X POST http://localhost:8000/auth/token
```
**Expected:**
```json
{"access_token": "dev-token", "token_type": "bearer"}
```
**What it proves:** Auth router is mounted, stub dependency returns without error.

---

## 3. Orgs

### 3.1 Create org (stub)
```powershell
curl -X POST http://localhost:8000/orgs `
  -H "Content-Type: application/json" `
  -d '{}'
```
**Expected status:** `201`
**Expected body:**
```json
{"message": "STUB — Phase 2: create org"}
```

### 3.2 Get org by ID (stub)
```powershell
curl http://localhost:8000/orgs/00000000-0000-0000-0000-000000000001
```
**Expected status:** `200`
**Expected body:**
```json
{"message": "STUB — Phase 2: get org", "org_id": "00000000-0000-0000-0000-000000000001"}
```

### 3.3 Invalid UUID returns 422
```powershell
curl http://localhost:8000/orgs/not-a-uuid
```
**Expected status:** `422`
**Expected body contains:** `"msg"` explaining UUID validation failure.

**What it proves:** FastAPI path parameter validation is active. The `UUID` type
annotation in the route signature is doing its job.

---

## 4. Events

### 4.1 Ingest event (stub)
```powershell
curl -X POST http://localhost:8000/orgs/00000000-0000-0000-0000-000000000001/events `
  -H "Content-Type: application/json" `
  -d '{}'
```
**Expected status:** `202`
**Expected body:**
```json
{"message": "STUB — Phase 2: ingest event", "org_id": "00000000-0000-0000-0000-000000000001"}
```

### 4.2 List events (stub)
```powershell
curl http://localhost:8000/orgs/00000000-0000-0000-0000-000000000001/events
```
**Expected status:** `200`
**Expected body:**
```json
{"message": "STUB — Phase 2: list events", "org_id": "00000000-0000-0000-0000-000000000001", "events": []}
```

### 4.3 Get single event (stub)
```powershell
curl http://localhost:8000/orgs/00000000-0000-0000-0000-000000000001/events/00000000-0000-0000-0000-000000000002
```
**Expected status:** `200`
**Expected body:**
```json
{"message": "STUB — Phase 2: get event", "event_id": "00000000-0000-0000-0000-000000000002"}
```

---

## 5. Artifacts

### 5.1 List artifacts (stub)
```powershell
curl http://localhost:8000/orgs/00000000-0000-0000-0000-000000000001/artifacts
```
**Expected status:** `200`
**Expected body:**
```json
{"message": "STUB — Phase 2: list artifacts", "org_id": "00000000-0000-0000-0000-000000000001", "artifacts": []}
```

---

## 6. Action Items

### 6.1 List action items (stub)
```powershell
curl http://localhost:8000/orgs/00000000-0000-0000-0000-000000000001/action-items
```
**Expected status:** `200`
**Expected body:**
```json
{"message": "STUB — Phase 2: list action items", "org_id": "00000000-0000-0000-0000-000000000001", "items": []}
```

### 6.2 Update action item (stub)
```powershell
curl -X PATCH http://localhost:8000/orgs/00000000-0000-0000-0000-000000000001/action-items/00000000-0000-0000-0000-000000000003 `
  -H "Content-Type: application/json" `
  -d '{}'
```
**Expected status:** `200`
**Expected body:**
```json
{"message": "STUB — Phase 2: update action item", "item_id": "00000000-0000-0000-0000-000000000003"}
```

---

## 7. Platform Links

### 7.1 Create platform link (stub)
```powershell
curl -X POST http://localhost:8000/orgs/00000000-0000-0000-0000-000000000001/platform-links `
  -H "Content-Type: application/json" `
  -d '{}'
```
**Expected status:** `201`
**Expected body:**
```json
{"message": "STUB — Phase 2: create platform link", "org_id": "00000000-0000-0000-0000-000000000001"}
```

### 7.2 List platform links (stub)
```powershell
curl http://localhost:8000/orgs/00000000-0000-0000-0000-000000000001/platform-links
```
**Expected status:** `200`
**Expected body:**
```json
{"message": "STUB — Phase 2: list platform links", "org_id": "00000000-0000-0000-0000-000000000001", "links": []}
```

---

## 8. Insights

### 8.1 Insights summary (stub)
```powershell
curl http://localhost:8000/orgs/00000000-0000-0000-0000-000000000001/insights/summary
```
**Expected status:** `200`
**Expected body:**
```json
{
  "org_id": "00000000-0000-0000-0000-000000000001",
  "period": "last_7_days",
  "total_events": 0,
  "total_action_items": 0,
  "open_action_items": 0,
  "active_members": 0,
  "top_topics": [],
  "message": "STUB — Phase 4: real insights from intelligence pipeline"
}
```

---

## 9. Session & DB Lifecycle

While running the HTTP calls above, watch the uvicorn terminal.

**Expected:** Only `INFO` lines for each request. No `ERROR`, no tracebacks,
no `rollback` messages.

Each request goes through `get_async_session()` in `api/deps.py` which:
1. Opens an `AsyncSession`
2. Yields it to the route handler
3. Commits on clean exit
4. Rolls back on exception
5. Closes the session

If any request shows a DB error in the terminal, the session lifecycle is broken.

---

## 10. Automated Code-Level Check

Run the verification script (covers models, repos, org isolation, crypto):

```powershell
make verify
```

**Expected output:**
```
13 passed  |  0 failed
```

This covers:
- All 11 SQLAlchemy models import correctly
- `Base.metadata` contains all 11 tables
- `OrgRepository` create / get_by_id / get_by_slug
- `OrgScopedRepository` cross-org isolation invariant
- Crypto `v1:<iv>:<tag>:<ct>` wire format
- Crypto round-trip encrypt → decrypt
- `is_encrypted` guard
- Random IV per encryption call
- Config reads `DATABASE_URL` correctly

---

## 11. Migration Cycle

```powershell
cd oracle

# Downgrade wipes all 11 tables
uv run alembic downgrade base

# Upgrade recreates them
uv run alembic upgrade head

# Confirm tables exist again
uv run python verify_phase01.py
```

**Expected:** `13 passed | 0 failed` after upgrade.
**What it proves:** The migration has no orphaned state — it is fully reversible.

---

## 12. 404 on Unknown Routes

```powershell
curl http://localhost:8000/does-not-exist
curl http://localhost:8000/orgs/00000000-0000-0000-0000-000000000001/does-not-exist
```

**Expected status:** `404` for both.
**What it proves:** FastAPI is not silently swallowing routing errors.

---

## Pass Criteria

| # | Check | Pass condition |
|---|---|---|
| 1.1 | Health | `{"status":"ok"}` |
| 1.2 | OpenAPI docs | 8 route groups visible |
| 2.1 | Auth token | `200`, stub token returned |
| 3.1 | Create org | `201` |
| 3.2 | Get org | `200`, org_id echoed back |
| 3.3 | Bad UUID | `422` |
| 4.1 | Ingest event | `202` |
| 4.2 | List events | `200`, empty list |
| 4.3 | Get event | `200` |
| 5.1 | List artifacts | `200`, empty list |
| 6.1 | List action items | `200`, empty list |
| 6.2 | Update action item | `200` |
| 7.1 | Create platform link | `201` |
| 7.2 | List platform links | `200`, empty list |
| 8.1 | Insights summary | `200`, all zero counts |
| 9 | No DB errors | Zero `ERROR` lines in server terminal |
| 10 | `make verify` | `13 passed | 0 failed` |
| 11 | Migration cycle | Downgrade + upgrade clean |
| 12 | 404s | Unknown routes return 404 |
