from __future__ import annotations
import asyncio,json,uuid
from datetime import datetime,timezone
from sqlalchemy import text
from app.domains.patient_engagement.schemas import CommunicationCreate
from app.domains.patient_engagement.service import CommunicationService
from app.domains.patient_engagement.providers import build_communication_provider
from app.domains.scheduling.repository import SchedulingRepository
from app.domains.scheduling.schemas import AppointmentUpdate
from app.domains.scheduling.service import SchedulingService
from app.domains.tasks.repository import TaskRepository
from app.domains.tasks.schemas import TaskCreate
from app.domains.tasks.service import TaskService
from app.domains.workflows.service import WorkflowService,SUPPORTED_STEP_TYPES
from app.infrastructure.database import tenant_session_context
from app.ai.governance.service import AIGovernanceService
MAX_STEPS=25
async def execute_run(organization_id:str,run_id:str):
 async with tenant_session_context(organization_id) as session:
  svc=WorkflowService(session); clinic_id=await svc.clinic_id(organization_id)
  run=(await session.execute(text('select wr.*,wv.definition from workflow_runs wr join workflow_versions wv on wv.id=wr.workflow_version_id where wr.id=:id and wr.clinic_id=:clinic'),{'id':run_id,'clinic':clinic_id})).mappings().first()
  if not run:return None
  if run['status']=='cancelled':return dict(run)
  worker_id=f"workflow:{uuid.uuid4()}"
  claimed=(await session.execute(text("""
    update workflow_runs
    set lease_owner=:worker,lease_expires_at=now()+interval '120 seconds',heartbeat_at=now(),updated_at=now()
    where id=:id and clinic_id=:clinic
      and (lease_owner is null or lease_expires_at<now() or lease_owner=:worker)
    returning *
  """),{'id':run_id,'clinic':clinic_id,'worker':worker_id})).mappings().first()
  if not claimed:return dict(run)
  run=dict(claimed)
  run['definition']=(await session.execute(text('select definition from workflow_versions where id=:version'),{'version':run['workflow_version_id']})).scalar_one()
  if run['status'] in {'queued','waiting_for_approval'}:await svc.transition(organization_id,run_id,'running')
  steps=(run['definition'] or {}).get('steps',[])
  if not isinstance(steps,list) or len(steps)>MAX_STEPS:raise ValueError('workflow exceeds maximum step count')
  try:
   for step in steps:
    key=step.get('key'); kind=step.get('type')
    if not key or kind not in SUPPORTED_STEP_TYPES:raise ValueError(f'unsupported workflow step: {kind}')
    state=(await session.execute(text('select id,status from workflow_step_runs where workflow_run_id=:run and step_key=:key'),{'run':run_id,'key':key})).mappings().first()
    if not state:raise ValueError(f'workflow step record missing: {key}')
    if state['status']=='completed':continue
    await session.execute(text("update workflow_runs set heartbeat_at=now(),lease_expires_at=now()+interval '120 seconds' where id=:run and clinic_id=:clinic and lease_owner=:worker"),{'run':run_id,'clinic':clinic_id,'worker':worker_id})
    await session.execute(text("update workflow_step_runs set status='running',attempts=attempts+1,lease_owner=:worker,lease_expires_at=now()+interval '120 seconds',heartbeat_at=now(),started_at=coalesce(started_at,now()) where workflow_run_id=:run and step_key=:key and (lease_owner is null or lease_expires_at<now() or lease_owner=:worker)"),{'run':run_id,'key':key,'worker':worker_id})
    if kind=='create_task':output={'task_id':(await TaskService(TaskRepository(session)).create(TaskCreate(**step.get('input',{}))))['id']}
    elif kind=='complete':output={'completed_at':datetime.now(timezone.utc).isoformat()}
    elif kind=='classify_message':
     from app.domains.patient_engagement.ai import MessageIntelligence
     output=(await MessageIntelligence().classify(str(step.get('input',{}).get('message','')),governance=AIGovernanceService(session,organization_id))).model_dump()
    elif kind=='update_appointment':
     inp=step.get('input',{}); appointment_id=inp.get('appointment_id')
     if not appointment_id:raise ValueError('appointment_id is required')
     output=await SchedulingService(SchedulingRepository(session)).update(appointment_id,AppointmentUpdate(**{k:v for k,v in inp.items() if k!='appointment_id'}))
    elif kind=='send_communication':
     inp=step.get('input',{}); payload={k:v for k,v in inp.items() if k not in {'approval_required','idempotency_key','workflow_run_id'}}; payload.update({'idempotency_key':inp.get('idempotency_key',f'{run_id}:{key}'),'workflow_run_id':run_id}); data=CommunicationCreate(**payload)
     if inp.get('approval_required'):
      approval=(await session.execute(text('select id,status from workflow_approvals where workflow_run_id=:run and workflow_step_run_id=:step order by created_at desc limit 1'),{'run':run_id,'step':state['id']})).mappings().first()
      if not approval:
       await session.execute(text("insert into workflow_approvals(id,clinic_id,workflow_run_id,workflow_step_run_id,requested_action,risk_level,status,requested_by,expires_at) values(gen_random_uuid()::text,:clinic,:run,:step,cast(:action as jsonb),'EXTERNAL_SIDE_EFFECT','pending',coalesce((select actor_id from workflow_runs where id=:run),'system'),now()+interval '30 minutes')"),{'clinic':clinic_id,'run':run_id,'step':state['id'],'action':json.dumps({'type':'send_communication','channel':data.channel,'patient_id':data.patient_id})}); await session.execute(text("update workflow_step_runs set status='waiting_for_approval' where id=:id"),{'id':state['id']}); await svc.transition(organization_id,run_id,'waiting_for_approval'); await session.execute(text("update workflow_runs set lease_owner=NULL,lease_expires_at=NULL,heartbeat_at=NULL,updated_at=now() where id=:id and clinic_id=:clinic"),{'id':run_id,'clinic':clinic_id}); return dict((await session.execute(text('select * from workflow_runs where id=:id'),{'id':run_id})).mappings().first())
      if approval['status']!='approved':await session.execute(text("update workflow_step_runs set status='waiting_for_approval' where id=:id"),{'id':state['id']}); await svc.transition(organization_id,run_id,'waiting_for_approval'); await session.execute(text("update workflow_runs set lease_owner=NULL,lease_expires_at=NULL,heartbeat_at=NULL,updated_at=now() where id=:id and clinic_id=:clinic"),{'id':run_id,'clinic':clinic_id}); return dict((await session.execute(text('select * from workflow_runs where id=:id'),{'id':run_id})).mappings().first())
     result=await CommunicationService(session,build_communication_provider()).queue(organization_id,data,run.get('request_id')); output={'communication_id':result['id'],'status':result['status']}
    elif kind=='request_approval':
     approval=(await session.execute(text('select id,status from workflow_approvals where workflow_run_id=:run and workflow_step_run_id=:step order by created_at desc limit 1'),{'run':run_id,'step':state['id']})).mappings().first()
     if not approval:
      inp=step.get('input',{}); risk=inp.get('risk_level','HIGH_RISK_WRITE')
      if risk not in {'READ','LOW_RISK_WRITE','HIGH_RISK_WRITE','EXTERNAL_SIDE_EFFECT'}:raise ValueError('invalid approval risk level')
      await session.execute(text("insert into workflow_approvals(id,clinic_id,workflow_run_id,workflow_step_run_id,requested_action,risk_level,status,requested_by,expires_at) values(gen_random_uuid()::text,:clinic,:run,:step,cast(:action as jsonb),:risk,'pending',coalesce((select actor_id from workflow_runs where id=:run),'system'),now()+interval '30 minutes')"),{'clinic':clinic_id,'run':run_id,'step':state['id'],'action':json.dumps(inp.get('action',{})),'risk':risk}); await session.execute(text("update workflow_step_runs set status='waiting_for_approval' where id=:id"),{'id':state['id']}); await svc.transition(organization_id,run_id,'waiting_for_approval'); await session.execute(text("update workflow_runs set lease_owner=NULL,lease_expires_at=NULL,heartbeat_at=NULL,updated_at=now() where id=:id and clinic_id=:clinic"),{'id':run_id,'clinic':clinic_id}); return dict((await session.execute(text('select * from workflow_runs where id=:id'),{'id':run_id})).mappings().first())
     if approval['status']=='approved':output={'approval_id':approval['id'],'status':'approved'}
     elif approval['status'] in {'rejected','expired','cancelled'}:raise RuntimeError(f'approval_{approval["status"]}')
     else:await session.execute(text("update workflow_step_runs set status='waiting_for_approval' where id=:id"),{'id':state['id']}); await svc.transition(organization_id,run_id,'waiting_for_approval'); await session.execute(text("update workflow_runs set lease_owner=NULL,lease_expires_at=NULL,heartbeat_at=NULL,updated_at=now() where id=:id and clinic_id=:clinic"),{'id':run_id,'clinic':clinic_id}); return dict((await session.execute(text('select * from workflow_runs where id=:id'),{'id':run_id})).mappings().first())
   await session.execute(text("update workflow_step_runs set status='completed',output=cast(:output as jsonb),lease_owner=NULL,lease_expires_at=NULL,heartbeat_at=NULL,completed_at=now() where workflow_run_id=:run and step_key=:key and lease_owner=:worker"),{'run':run_id,'key':key,'worker':worker_id,'output':json.dumps(output,default=str)})
   await svc.transition(organization_id,run_id,'completed'); await session.execute(text("update workflow_runs set result=cast(:result as jsonb),lease_owner=NULL,lease_expires_at=NULL,heartbeat_at=NULL,updated_at=now() where id=:id and clinic_id=:clinic and lease_owner=:worker"),{'result':json.dumps({'steps':len(steps)}),'id':run_id,'clinic':clinic_id,'worker':worker_id}); return dict((await session.execute(text('select * from workflow_runs where id=:id'),{'id':run_id})).mappings().first())
  except Exception as exc:
   await session.execute(text("update workflow_step_runs set status='failed',error_class=:error,lease_owner=NULL,lease_expires_at=NULL,heartbeat_at=NULL,completed_at=now() where workflow_run_id=:run and status='running' and lease_owner=:worker"),{'run':run_id,'error':type(exc).__name__,'worker':worker_id}); await session.execute(text("update workflow_runs set failure_class=:error,lease_owner=NULL,lease_expires_at=NULL,heartbeat_at=NULL,updated_at=now() where id=:run and clinic_id=:clinic and lease_owner=:worker"),{'run':run_id,'error':type(exc).__name__,'clinic':clinic_id,'worker':worker_id}); current=(await session.execute(text('select status from workflow_runs where id=:id'),{'id':run_id})).scalar_one()
   if current in {'running','waiting_for_approval'}:await svc.transition(organization_id,run_id,'failed')
   return dict((await session.execute(text('select * from workflow_runs where id=:id'),{'id':run_id})).mappings().first())
def execute_run_sync(organization_id:str,run_id:str):return asyncio.run(execute_run(organization_id,run_id))
