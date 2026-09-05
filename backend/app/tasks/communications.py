from app.tasks.celery import celery_app
from app.domains.patient_engagement.outbox import process_communication_outbox
@celery_app.task(bind=True,acks_late=True,autoretry_for=(),max_retries=0,time_limit=120,soft_time_limit=90)
def dispatch_communication_outbox(self,organization_id:str): return __import__('asyncio').run(process_communication_outbox(organization_id))
