from celery import Celery
from app.core.config import settings
celery_app=Celery('hezqara',broker=settings.redis_url,backend=settings.redis_url,include=['app.tasks.workflows','app.tasks.communications'])
celery_app.conf.update(task_acks_late=True,task_reject_on_worker_lost=True,task_track_started=True,task_time_limit=300,task_soft_time_limit=240,task_default_queue='hezqara',task_routes={'app.tasks.workflows.execute_workflow_run':{'queue':'hezqara'},'app.tasks.communications.dispatch_communication_outbox':{'queue':'hezqara'}})
