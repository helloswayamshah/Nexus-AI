"""
Unit tests for app.core.queue (AsyncTaskQueue)

Pure async unit tests — no DB or server needed.
Verifies job enqueue, handler dispatch, status tracking,
error handling, and concurrency limiting.
"""

import asyncio
import pytest
from app.core.queue import AsyncTaskQueue, JobStatus


# ── Enqueue & dispatch ────────────────────────────────────────────────────

class TestEnqueueAndDispatch:
    async def test_enqueue_returns_job_id(self):
        q = AsyncTaskQueue()
        q.register_handler("echo", lambda p: asyncio.sleep(0))
        job_id = await q.enqueue("echo", {"x": 1})
        assert isinstance(job_id, str) and len(job_id) > 0

    async def test_handler_receives_payload(self):
        received = {}

        async def capture(payload):
            received.update(payload)

        q = AsyncTaskQueue()
        q.register_handler("capture", capture)
        await q.enqueue("capture", {"key": "value"})
        await asyncio.sleep(0.05)
        assert received == {"key": "value"}

    async def test_completed_job_status(self):
        q = AsyncTaskQueue()
        q.register_handler("noop", lambda p: asyncio.sleep(0))
        job_id = await q.enqueue("noop", {})
        await asyncio.sleep(0.05)
        job = q.get_status(job_id)
        assert job.status == JobStatus.COMPLETED

    async def test_handler_return_value_stored_in_result(self):
        async def add(payload):
            return payload["a"] + payload["b"]

        q = AsyncTaskQueue()
        q.register_handler("add", add)
        job_id = await q.enqueue("add", {"a": 2, "b": 3})
        await asyncio.sleep(0.05)
        assert q.get_status(job_id).result == 5

    async def test_multiple_jobs_all_complete(self):
        results = []

        async def collect(payload):
            results.append(payload["n"])

        q = AsyncTaskQueue()
        q.register_handler("collect", collect)
        for i in range(5):
            await q.enqueue("collect", {"n": i})
        await asyncio.sleep(0.1)
        assert sorted(results) == [0, 1, 2, 3, 4]


# ── Error handling ────────────────────────────────────────────────────────

class TestErrorHandling:
    async def test_failed_job_status(self):
        async def boom(_):
            raise ValueError("something went wrong")

        q = AsyncTaskQueue()
        q.register_handler("boom", boom)
        job_id = await q.enqueue("boom", {})
        await asyncio.sleep(0.05)
        job = q.get_status(job_id)
        assert job.status == JobStatus.FAILED

    async def test_failed_job_stores_error_message(self):
        async def boom(_):
            raise ValueError("something went wrong")

        q = AsyncTaskQueue()
        q.register_handler("boom", boom)
        job_id = await q.enqueue("boom", {})
        await asyncio.sleep(0.05)
        assert "something went wrong" in q.get_status(job_id).error

    async def test_one_failure_does_not_affect_other_jobs(self):
        results = []

        async def boom(_):
            raise RuntimeError("fail")

        async def ok(payload):
            results.append(payload["v"])

        q = AsyncTaskQueue()
        q.register_handler("boom", boom)
        q.register_handler("ok", ok)
        await q.enqueue("boom", {})
        await q.enqueue("ok", {"v": 42})
        await asyncio.sleep(0.1)
        assert 42 in results

    async def test_enqueue_unknown_type_raises(self):
        q = AsyncTaskQueue()
        with pytest.raises(ValueError, match="No handler registered"):
            await q.enqueue("unknown_type", {})


# ── get_status ────────────────────────────────────────────────────────────

class TestGetStatus:
    async def test_returns_none_for_unknown_job_id(self):
        q = AsyncTaskQueue()
        assert q.get_status("does-not-exist") is None

    async def test_job_starts_as_pending(self):
        arrived = asyncio.Event()
        proceed = asyncio.Event()

        async def slow(_):
            arrived.set()
            await proceed.wait()

        q = AsyncTaskQueue()
        q.register_handler("slow", slow)
        job_id = await q.enqueue("slow", {})
        # Job is pending until the handler coroutine is scheduled
        job = q.get_status(job_id)
        assert job.status in (JobStatus.PENDING, JobStatus.RUNNING)
        proceed.set()


# ── Concurrency ───────────────────────────────────────────────────────────

class TestConcurrency:
    async def test_respects_max_concurrency(self):
        active = 0
        max_seen = 0

        async def track(_):
            nonlocal active, max_seen
            active += 1
            max_seen = max(max_seen, active)
            await asyncio.sleep(0.02)
            active -= 1

        q = AsyncTaskQueue(max_concurrency=2)
        q.register_handler("track", track)
        for _ in range(6):
            await q.enqueue("track", {})
        await asyncio.sleep(0.3)
        assert max_seen <= 2
