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
