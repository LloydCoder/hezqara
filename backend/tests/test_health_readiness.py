import asyncio
import json
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from app.api.v1 import health


@asynccontextmanager
async def ready_session():
    yield object()


class UnavailableSession:
    async def __aenter__(self):
        raise RuntimeError("database connection details must not be exposed")

    async def __aexit__(self, exc_type, exc, traceback):
        return False


def test_readiness_returns_200_only_when_all_dependencies_are_healthy(monkeypatch):
    async def fake_readiness(_session):
        return {
            "status": "ready",
            "checks": {
                "database": "ok",
                "durable_jobs": "ok",
                "worker_heartbeat": "ok",
            },
            "generated_at": datetime(2026, 10, 15, tzinfo=timezone.utc),
        }

    monkeypatch.setattr(health, "system_session_context", ready_session)
    monkeypatch.setattr(health, "readiness", fake_readiness)

    response = asyncio.run(health.ready())

    assert response.status_code == 200
    payload = json.loads(response.body)
    assert payload["status"] == "ready"
    assert set(payload["checks"].values()) == {"ok"}
    assert response.headers["cache-control"] == "no-store"


def test_readiness_returns_503_when_worker_is_degraded(monkeypatch):
    async def fake_readiness(_session):
        return {
            "status": "degraded",
            "checks": {
                "database": "ok",
                "durable_jobs": "ok",
                "worker_heartbeat": "degraded",
            },
        }

    monkeypatch.setattr(health, "system_session_context", ready_session)
    monkeypatch.setattr(health, "readiness", fake_readiness)

    response = asyncio.run(health.ready())

    assert response.status_code == 503
    payload = json.loads(response.body)
    assert payload["status"] == "degraded"
    assert payload["checks"]["worker_heartbeat"] == "degraded"


def test_readiness_fails_closed_without_leaking_connection_errors(monkeypatch):
    async def unused_readiness(_session):
        raise AssertionError("readiness must not run without a database session")

    monkeypatch.setattr(health, "system_session_context", lambda: UnavailableSession())
    monkeypatch.setattr(health, "readiness", unused_readiness)

    response = asyncio.run(health.ready())

    assert response.status_code == 503
    payload = json.loads(response.body)
    assert payload == {
        "status": "degraded",
        "checks": {
            "database": "unavailable",
            "durable_jobs": "unavailable",
            "worker_heartbeat": "unavailable",
        },
    }
    assert "connection details" not in response.body.decode()



def test_readiness_handles_worker_probe_failure_independently():
    from app.platform.reliability import readiness

    class Result:
        def scalar_one(self):
            return 1

    class WorkerProbeFailureSession:
        async def execute(self, statement):
            if "healthy_worker_count" in str(statement):
                raise RuntimeError("worker heartbeat function unavailable")
            return Result()

    result = asyncio.run(readiness(WorkerProbeFailureSession()))

    assert result["status"] == "degraded"
    assert result["checks"] == {
        "database": "ok",
        "durable_jobs": "ok",
        "worker_heartbeat": "unavailable",
    }
