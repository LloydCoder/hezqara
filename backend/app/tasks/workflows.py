from app.tasks.celery import celery_app
from app.domains.workflows.runtime import execute_run_sync

@celery_app.task(bind=True,acks_late=True,autoretry_for=(),max_retries=0,time_limit=300,soft_time_limit=240)
def execute_workflow_run(self,clinic_id:str,run_id:str):
    return execute_run_sync(clinic_id,run_id)
