from app.tasks.celery import celery_app
@celery_app.task(bind=True,autoretry_for=(Exception,),retry_backoff=True,max_retries=5)
def send_patient_engagement(self, tenant_id:str, workflow_id:str):
    return {"tenant_id":tenant_id,"workflow_id":workflow_id,"status":"queued"}
