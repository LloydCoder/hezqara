from __future__ import annotations
import asyncio, json
from datetime import datetime
from sqlalchemy import text
from app.domains.tasks.repository import TaskRepository
from app.domains.tasks.schemas import TaskCreate
from app.domains.tasks.service import TaskService
from app.infrastructure.database import tenant_session_context
from app.security.audit import append_event
from app.domains.workflows.service import WorkflowService

SUPPORTED_STEPS={'create_task','complete'}

async def execute_run(clinic_id:str, run_id:str):
    async with tenant_session_context(clinic_id) as session:
        svc=WorkflowService(session)
        run=(await session.execute(text('select wr.*,wv.definition from workflow_runs wr join workflow_versions wv on wv.id=wr.workflow_version_id where wr.id=:id and wr.clinic_id=:clinic'),{'id':run_id,'clinic':clinic_id})).mappings().first()
        if not run: return None
        if run['status']=='cancelled': return dict(run)
        await svc.transition(clinic_id,run_id,'running')
        definition=run['definition'] or {}
        try:
            for step in definition.get('steps',[]):
                key=step['key']; kind=step.get('type')
                if kind not in SUPPORTED_STEPS: raise ValueError(f'unsupported workflow step: {kind}')
                await session.execute(text("update workflow_step_runs set status='running',attempts=attempts+1,started_at=now() where workflow_run_id=:run and step_key=:key"),{'run':run_id,'key':key})
                if kind=='create_task':
                    payload=step.get('input',{})
                    task=await TaskService(TaskRepository(session)).create(TaskCreate(**payload))
                    output={'task_id':task['id']}
                else:
                    output={'completed_at':datetime.now().isoformat()}
                await session.execute(text("update workflow_step_runs set status='completed',output=cast(:output as jsonb),completed_at=now() where workflow_run_id=:run and step_key=:key"),{'run':run_id,'key':key,'output':json.dumps(output)})
                await append_event(session,organization_id=clinic_id,actor=run['actor_id'],action='workflow.step.completed',resource_type='workflow_step',resource_id=key,outcome='success',request_id=run['request_id'],metadata={'workflow_run_id':run_id})
            return await svc.transition(clinic_id,run_id,'completed')
        except Exception as exc:
            await session.execute(text("update workflow_step_runs set status='failed',error_class=:error,completed_at=now() where workflow_run_id=:run and status='running'"),{'run':run_id,'error':type(exc).__name__})
            await session.execute(text("update workflow_runs set failure_class=:error,updated_at=now() where id=:run and clinic_id=:clinic"),{'run':run_id,'error':type(exc).__name__,'clinic':clinic_id})
            return await svc.transition(clinic_id,run_id,'failed')

def execute_run_sync(clinic_id:str,run_id:str):
    return asyncio.run(execute_run(clinic_id,run_id))
