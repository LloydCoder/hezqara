from celery import Celery
from app.core.config import settings
celery_app=Celery("hezqara",broker=settings.redis_url,backend=settings.redis_url)
celery_app.conf.update(task_acks_late=True,task_reject_on_worker_lost=True,task_track_started=True,task_time_limit=300,task_soft_time_limit=240)
