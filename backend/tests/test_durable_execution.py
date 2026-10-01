from app.tasks.celery import celery_app

def test_durable_execution_routes_are_registered():
    routes=celery_app.conf.task_routes
    assert "app.tasks.durable.run_platform_job" in routes
    assert "app.tasks.durable.dispatch_due_platform_jobs" in routes
    assert "app.tasks.durable.reconcile_execution_leases" in routes

def test_durable_recovery_schedule_is_present():
    schedule=celery_app.conf.beat_schedule
    assert schedule["dispatch-durable-jobs"]["schedule"] == 15.0
    assert schedule["reconcile-execution-leases"]["schedule"] == 30.0

def test_late_ack_and_worker_loss_recovery_are_enabled():
    assert celery_app.conf.task_acks_late is True
    assert celery_app.conf.task_reject_on_worker_lost is True


def test_durable_workflow_job_awaits_async_runtime(monkeypatch):
    import asyncio
    from app.tasks import durable

    class SessionContext:
        async def __aenter__(self):
            return object()
        async def __aexit__(self, exc_type, exc, tb):
            return False

    class Jobs:
        def __init__(self, session):
            pass
        async def claim(self, job_id, worker_id):
            return {"id": job_id, "job_type": "workflow.execute", "payload": {"organization_id": "org", "run_id": "run"}}
        async def complete(self, job_id, worker_id, result):
            return True

    async def fake_execute_run(organization_id, run_id):
        return {"status": "waiting_for_approval", "organization_id": organization_id, "run_id": run_id}

    monkeypatch.setattr(durable, "system_session_context", lambda: SessionContext())
    monkeypatch.setattr(durable, "DurableJobService", Jobs)
    monkeypatch.setattr(durable, "execute_run", fake_execute_run)

    result = asyncio.run(durable._run_platform_job("job-1"))

    assert result["status"] == "completed"
    assert result["result"]["result"]["status"] == "waiting_for_approval"
