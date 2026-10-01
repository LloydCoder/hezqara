from celery import Celery
from celery.schedules import crontab
from app.core.config import settings
celery_app=Celery('hezqara',broker=settings.redis_url,backend=settings.redis_url,include=['app.tasks.workflows','app.tasks.communications','app.tasks.durable'])
celery_app.conf.update(
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_track_started=True,
    task_time_limit=300,
    task_soft_time_limit=240,
    task_default_queue='hezqara',
    task_routes={
        'app.tasks.workflows.execute_workflow_run':{'queue':'hezqara'},
        'app.tasks.communications.dispatch_communication_outbox':{'queue':'hezqara'},
        'app.tasks.durable.run_platform_job':{'queue':'hezqara'},
        'app.tasks.durable.dispatch_due_platform_jobs':{'queue':'hezqara'},
        'app.tasks.durable.reconcile_execution_leases':{'queue':'hezqara'},
    },
    beat_schedule={
        'dispatch-durable-jobs':{'task':'app.tasks.durable.dispatch_due_platform_jobs','schedule':15.0},
        'reconcile-execution-leases':{'task':'app.tasks.durable.reconcile_execution_leases','schedule':30.0},
    },
    timezone='UTC',
)
