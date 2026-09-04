"""
Tests for Redis-backed OfflineSyncQueue.

Fixes confirmed gap: the original implementation was pure in-memory
(`self._queue: list = []`), meaning every queued operation was lost on
a process restart — which is exactly when this feature matters most,
since Nigerian hospitals cite power outages as the #1 infrastructure
challenge. A clinic's server restarting during a power cut must not
silently lose queued patient check-ins.

Design: Redis is the source of truth when available. If Redis is
unreachable (itself offline, e.g. during initial setup), falls back
to in-memory so the app never crashes — but logs a clear warning since
that fallback loses the durability guarantee.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestRedisBackedSyncQueue:

    @pytest.mark.asyncio
    async def test_enqueue_persists_to_redis(self):
        """Operations must be written to Redis, not just memory."""
        from app.standalone.sync import OfflineSyncQueue

        mock_redis = AsyncMock()
        queue = OfflineSyncQueue(clinic_id="clinic_ng_001", redis_client=mock_redis)

        await queue.enqueue({
            "operation": "create_patient",
            "data": {"first_name": "Amaka"},
        })

        mock_redis.rpush.assert_called_once()
        call_args = mock_redis.rpush.call_args
        assert "clinic_ng_001" in call_args[0][0]  # key includes clinic_id

    @pytest.mark.asyncio
    async def test_get_pending_reads_from_redis(self):
        """Pending operations must be read back from Redis, surviving a restart."""
        from app.standalone.sync import OfflineSyncQueue
        import json

        stored_op = json.dumps({
            "id": "op1", "clinic_id": "clinic_ng_001",
            "operation": "create_patient", "data": {"first_name": "Amaka"},
        })

        mock_redis = AsyncMock()
        mock_redis.lrange = AsyncMock(return_value=[stored_op.encode()])

        queue = OfflineSyncQueue(clinic_id="clinic_ng_001", redis_client=mock_redis)
        pending = await queue.get_pending()

        assert len(pending) == 1
        assert pending[0]["operation"] == "create_patient"

    @pytest.mark.asyncio
    async def test_sync_all_removes_from_redis_on_success(self):
        """Successfully synced operations must be removed from the Redis queue."""
        from app.standalone.sync import OfflineSyncQueue
        import json

        stored_op = json.dumps({
            "id": "op1", "clinic_id": "clinic_ng_001",
            "operation": "create_patient", "data": {},
        })

        mock_redis = AsyncMock()
        mock_redis.lrange = AsyncMock(return_value=[stored_op.encode()])
        mock_redis.lrem = AsyncMock()

        queue = OfflineSyncQueue(clinic_id="clinic_ng_001", redis_client=mock_redis)

        with patch.object(queue, "_sync_to_db", return_value=True):
            result = await queue.sync_all()

        assert result["synced"] == 1
        mock_redis.lrem.assert_called_once()

    @pytest.mark.asyncio
    async def test_falls_back_to_memory_when_redis_unreachable(self):
        """
        If Redis itself is down, must not crash — falls back to in-memory
        with a logged warning. This is a degraded mode, not a failure mode.
        """
        from app.standalone.sync import OfflineSyncQueue

        mock_redis = AsyncMock()
        mock_redis.rpush = AsyncMock(side_effect=ConnectionError("Redis unreachable"))

        queue = OfflineSyncQueue(clinic_id="clinic_ng_001", redis_client=mock_redis)

        # Must not raise — falls back gracefully
        await queue.enqueue({"operation": "create_patient", "data": {}})

        pending = await queue.get_pending()
        assert len(pending) == 1  # Still tracked in memory fallback

    @pytest.mark.asyncio
    async def test_queue_survives_simulated_restart(self):
        """
        Simulates a process restart: a NEW OfflineSyncQueue instance for the
        same clinic, backed by the same Redis, must see operations enqueued
        by the OLD instance. This is the core durability guarantee.
        """
        from app.standalone.sync import OfflineSyncQueue
        import json

        # Shared "Redis" state across both instances
        fake_redis_store = []

        mock_redis = AsyncMock()
        mock_redis.rpush = AsyncMock(
            side_effect=lambda key, val: fake_redis_store.append(val)
        )
        mock_redis.lrange = AsyncMock(
            side_effect=lambda key, start, end: fake_redis_store
        )

        # "Before restart"
        queue1 = OfflineSyncQueue(clinic_id="clinic_ng_001", redis_client=mock_redis)
        await queue1.enqueue({"operation": "create_patient", "data": {"first_name": "Amaka"}})

        # "After restart" — brand new instance, same clinic, same Redis
        queue2 = OfflineSyncQueue(clinic_id="clinic_ng_001", redis_client=mock_redis)
        pending = await queue2.get_pending()

        assert len(pending) == 1
        assert pending[0]["data"]["first_name"] == "Amaka"

    @pytest.mark.asyncio
    async def test_no_redis_client_defaults_to_memory_only(self):
        """Backward compatible: no redis_client passed → pure in-memory, as before."""
        from app.standalone.sync import OfflineSyncQueue

        queue = OfflineSyncQueue(clinic_id="clinic_ng_001")
        await queue.enqueue({"operation": "create_patient", "data": {}})
        pending = await queue.get_pending()
        assert len(pending) == 1
