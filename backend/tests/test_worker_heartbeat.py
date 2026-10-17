import asyncio
from contextlib import asynccontextmanager

from app.tasks import durable
from app.tasks.celery import celery_app


def test_worker_heartbeat_records_a_fresh_heartbeat(monkeypatch):
    calls = []

    @asynccontextmanager
    async def fake_session_context():
        yield object()

    async def fake_record_worker_heartbeat(
        session, worker_id, queue, active_jobs=0, version=None
    ):
        calls.append(
            {
                "session": session,
                "worker_id": worker_id,
                "queue": queue,
                "active_jobs": active_jobs,
                "version": version,
            }
        )

    monkeypatch.setattr(durable, "system_session_context", fake_session_context)
    monkeypatch.setattr(
        durable, "record_worker_heartbeat", fake_record_worker_heartbeat
    )

    result = asyncio.run(durable._heartbeat_worker())

    assert result["status"] == "ok"
    assert result["worker_id"]
    assert len(calls) == 1
    assert calls[0]["worker_id"] == result["worker_id"]
    assert calls[0]["queue"] == "hezqara"
    assert calls[0]["active_jobs"] == 0


def test_worker_heartbeat_is_scheduled_on_the_worker_queue():
    schedule = celery_app.conf.beat_schedule["heartbeat-worker"]

    assert schedule["task"] == "app.tasks.durable.heartbeat_worker"
    assert schedule["schedule"] == 30.0
    assert (
        celery_app.conf.task_routes["app.tasks.durable.heartbeat_worker"]
        == {"queue": "hezqara"}
    )
