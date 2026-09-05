from __future__ import annotations
import json
import uuid
from typing import Any
from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

LEGAL_RUN_TRANSITIONS = {
    'queued': {'running','cancelled'},
    'running': {'waiting_for_approval','completed','failed','escalated','cancelled'},
    'waiting_for_approval': {'running','failed','escalated','cancelled'},
    'failed': {'queued','cancelled'},
    'escalated': {'queued','cancelled'},
    'completed': set(),
    'cancelled': set(),
}

class WorkflowService:
    def __init__(self, session: AsyncSession): self.session = session

    async def list(self, limit: int, offset: int):
        result = await self.session.execute(text("select id,key,name,description,status,created_at,updated_at from workflows order by updated_at desc,id desc limit :limit offset :offset"), {'limit': limit, 'offset': offset})
        return [dict(r) for r in result.mappings()]

    async def create(self, clinic_id: str, user_id: str, key: str, name: str, description: str | None, definition: dict[str, Any]):
        workflow_id = str(uuid.uuid4()); version_id = str(uuid.uuid4())
        await self.session.execute(text("insert into workflows(id,clinic_id,key,name,description,created_by) values(:id,:clinic,:key,:name,:description,:user)"), {'id':workflow_id,'clinic':clinic_id,'key':key,'name':name,'description':description,'user':user_id})
        await self.session.execute(text("insert into workflow_versions(id,workflow_id,version,definition,created_by) values(:id,:workflow,1,cast(:definition as jsonb),:user)"), {'id':version_id,'workflow':workflow_id,'definition':json.dumps(definition),'user':user_id})
        return await self.get(workflow_id)

    async def get(self, workflow_id: str):
        result = await self.session.execute(text("select id,key,name,description,status,created_at,updated_at from workflows where id=:id"), {'id':workflow_id})
        row = result.mappings().first()
        if not row: raise HTTPException(status_code=404, detail='workflow not found')
        return dict(row)

    async def activate(self, workflow_id: str):
        current = await self.get(workflow_id)
        if current['status'] == 'archived': raise HTTPException(status_code=409, detail='archived workflow cannot be activated')
        await self.session.execute(text("update workflows set status='active',updated_at=now() where id=:id"), {'id':workflow_id})
        await self.session.execute(text("update workflow_versions set activated_at=coalesce(activated_at,now()) where workflow_id=:id and version=(select max(version) from workflow_versions where workflow_id=:id)"), {'id':workflow_id})
        return await self.get(workflow_id)

    async def trigger(self, clinic_id: str, user_id: str, workflow_id: str, trigger_type: str, idempotency_key: str, context: dict[str, Any], request_id: str | None):
        workflow = await self.get(workflow_id)
        if workflow['status'] != 'active': raise HTTPException(status_code=409, detail='workflow is not active')
        version = await self.session.execute(text("select id,version,definition from workflow_versions where workflow_id=:id and activated_at is not null order by version desc limit 1"), {'id':workflow_id})
        version_row = version.mappings().first()
        if not version_row: raise HTTPException(status_code=409, detail='workflow has no active version')
        existing = await self.session.execute(text("select * from workflow_runs where workflow_id=:workflow and clinic_id=:clinic and idempotency_key=:key"), {'workflow':workflow_id,'clinic':clinic_id,'key':idempotency_key})
        row = existing.mappings().first()
        if row: return dict(row)
        run_id = str(uuid.uuid4())
        await self.session.execute(text("insert into workflow_runs(id,clinic_id,workflow_id,workflow_version_id,status,trigger_type,actor_id,request_id,idempotency_key,context) values(:id,:clinic,:workflow,:version,'queued',:trigger,:actor,:request,:key,cast(:context as jsonb))"), {'id':run_id,'clinic':clinic_id,'workflow':workflow_id,'version':version_row['id'],'trigger':trigger_type,'actor':user_id,'request':request_id,'key':idempotency_key,'context':json.dumps(context)})
        definition = version_row['definition'] or {}
        for ordinal, step in enumerate(definition.get('steps', [])):
            step_key = step.get('key')
            if not step_key: raise HTTPException(status_code=422, detail='workflow step key required')
            await self.session.execute(text("insert into workflow_step_runs(workflow_run_id,step_key,ordinal,input) values(:run,:key,:ordinal,cast(:input as jsonb))"), {'run':run_id,'key':step_key,'ordinal':ordinal,'input':json.dumps(step.get('input',{}))})
        await self.session.execute(text("insert into workflow_events(id,clinic_id,workflow_run_id,event_type,actor_id,request_id,aggregate_type,aggregate_id) values(:id,:clinic,:run,'workflow.run.created',:actor,:request,'workflow_run',:run)"), {'id':str(uuid.uuid4()),'clinic':clinic_id,'run':run_id,'actor':user_id,'request':request_id})
        result = await self.session.execute(text("select * from workflow_runs where id=:id"), {'id':run_id})
        return dict(result.mappings().first())

    async def transition(self, clinic_id: str, run_id: str, target: str):
        result = await self.session.execute(text("select status from workflow_runs where id=:id and clinic_id=:clinic for update"), {'id':run_id,'clinic':clinic_id})
        row = result.mappings().first()
        if not row: raise HTTPException(status_code=404, detail='workflow run not found')
        if target not in LEGAL_RUN_TRANSITIONS.get(row['status'], set()): raise HTTPException(status_code=409, detail='invalid workflow run state transition')
        terminal = target in {'completed','failed','escalated','cancelled'}
        await self.session.execute(text("update workflow_runs set status=:target,started_at=case when :target='running' and started_at is null then now() else started_at end,completed_at=case when :terminal then now() else completed_at end,updated_at=now() where id=:id and clinic_id=:clinic"), {'target':target,'terminal':terminal,'id':run_id,'clinic':clinic_id})
        return dict((await self.session.execute(text("select * from workflow_runs where id=:id"), {'id':run_id})).mappings().first())
