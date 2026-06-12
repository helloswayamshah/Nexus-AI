# Pull Request Testing Guide

This guide provides technical validation steps for the two primary PRs in the Nexus Oracle migration.

---

## 📦 [PR #4] Phase 1 & 2: Oracle API Core
**Focus:** Database schema, Org management, and Platform resolution.

### 1. Database & Health
- **Command:** `cd oracle; poetry run alembic upgrade head`
- **Expectation:** Migrations run successfully, creating 11 tables in Postgres/SQLite.
- **Verification:** Run `poetry run uvicorn app.main:app` and visit `http://localhost:8000/health`. Should return `{"status": "ok"}`.

### 2. Org & Link Setup (The "Resolution" Flow)
We must verify that an adapter can find its Org based on a Platform ID.
1. **Create Org:**
   ```bash
   curl -X POST http://localhost:8000/orgs/ \
     -H "Content-Type: application/json" \
     -d '{"name": "Test Lab", "slug": "test-lab"}'
   ```
   *Copy the `id` from the response.*
2. **Link Platform:**
   ```bash
   curl -X POST http://localhost:8000/orgs/{ORG_ID}/platform-links \
     -H "Content-Type: application/json" \
     -d '{"platform": "discord", "external_id": "my-guild-123", "config_json": {"llm_model": "llama3.1"}}'
   ```
3. **Test Resolution:**
   ```bash
   curl http://localhost:8000/orgs/platform-links/resolve/discord/my-guild-123
   ```
   *Expectation:* Returns the `ORG_ID` and the `config_json` we just set.

---

## 🚀 [PR #5] Phase 3-5: Full Integration & Brain
**Focus:** Stateless adapters, Async background tasks, and Docker orchestration.

### 1. Stateless Adapter Startup
1. Set `USE_ORACLE=true` in `.env`.
2. Delete your local `data/bot.db` (to prove it's not needed).
3. Start the Discord adapter: `node adapters/discord/src/index.js`.
4. **Verification:** The bot should start successfully and log: `[core:oracle] fetching config for discord:...`. It should successfully resolve the settings from Step 2 above.

### 2. Intelligence Pipeline (The "Brain")
Test that posting an event triggers a background summary.
1. **Ingest Event:**
   ```bash
   curl -X POST http://localhost:8000/orgs/{ORG_ID}/events \
     -H "Content-Type: application/json" \
     -d '{
       "platform": "discord",
       "event_type": "VOICE_CALL",
       "external_id": "call-001",
       "occurred_at": "2026-05-15T15:00:00Z",
       "raw_content": {"transcript": "User: This is a test of the emergency brain system."}
     }'
   ```
2. **Check Logs:** The Oracle terminal should show: `INFO: Processing event ...` followed by `INFO: Summary generated`.
3. **Verify Result:**
   ```bash
   curl http://localhost:8000/orgs/{ORG_ID}/artifacts
   ```
   *Expectation:* A `SUMMARY` artifact exists containing a summary of your test transcript.

### 3. Docker Orchestration
1. **Command:** `docker compose up --build -d`
2. **Verify Services:**
   ```bash
   docker compose ps
   ```
   *Expectation:* `nexus-oracle`, `nexus-discord`, `nexus-slack`, and `nexus-postgres` all show `Up (healthy)`.
3. **End-to-End Voice:**
   - Join Discord VC. speak, then `/leave`.
   - Verify summary appears in Discord AND a new entry appears in the Oracle's `GET /events` list.

---
> [!IMPORTANT]
> If testing **Ollama** inside Docker, ensure the `nexus-ollama-init` service has finished pulling the model (`docker logs nexus-ollama-init`) before running summarization tests.
