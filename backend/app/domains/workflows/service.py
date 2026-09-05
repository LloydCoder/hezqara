from __future__ import annotations
import json,uuid
from typing import Any
from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
SUPPORTED_STEP_TYPES={'create_task','complete','send_communication','request_approval','classify_message','update_appointment'}
LEGAL_RUN_TRANSITIONS={'queued':{'running','cancelled'},'running':{'waiting_for_approval','completed','failed','escalated','cancelled'},'waiting_for_approval':{'running','failed','escalated','cancelled'},'failed':{'queued','cancelled'},'escalated':{'queued','cancelled'},'completed':set(),'cancelled':set()}
class WorkflowService:
    def __init__(self,session:AsyncSession): self.session=session
    async def clinic_id(self,organization_id:str)->str:
        row=(await self.session.execute(text('select id from clinics where clerk_org_id=:org'),{'org':organization_id})).scalar_one_or_none()
        if not row: raise HTTPException(status_code=404,detail='organization clinic not found')
        return str(row)
    async def list(self,limit:int,offset:int):
        result=await self.session.execute(text('select id,key,name,description,status,created_at,updated_at from workflows order by updated_at desc,id desc limit :limit offset :offset'),{'limit':limit,'offset':offset}); return [dict(r) for r in result.mappings()]
    async def create(self,organization_id:str,user_id:str,key:str,name:str,description:str|None,definition:dict[str,Any]):
        clinic=await self.clinic_id(organization_id); workflow_id=str(uuid.uuid4()); version_id=str(uuid.uuid4()); steps=definition.get('steps',[])
        if not isinstance(steps,list) or len(steps)>25: raise HTTPException(status_code=422,detail='workflow steps must be a list of at most 25 steps')
        seen=set()
        for step in steps:
            if not isinstance(step,dict) or not isinstance(step.get('key'),str) or step['key'] in seen or len(step['key'])>100 or step.get('type') not in SUPPORTED_STEP_TYPES: raise HTTPException(status_code=422,detail='invalid or unsupported workflow step')
            seen.add(step['key'])
        await self.session.execute(text('insert into workflows(id,clinic_id,key,name,description,created_by) values(:id,:clinic,:key,:name,:description,:user)'),{'id':workflow_id,'clinic':clinic,'key':key,'name':name,'description':description,'user':user_id})
        await self.session.execute(text('insert into workflow_versions(id,workflow_id,version,definition,created_by) values(:id,:workflow,1,cast(:definition as jsonb),:user)'),{'id':version_id,'workflow':workflow_id,'definition':json.dumps(definition),'user':user_id}); return await self.get(workflow_id)
    async def get(self,workflow_id:str):
        row=(await self.session.execute(text("select id,key,name,description,status,created_at,updated_at from workflows where id=:id and clinic_id in (select id from clinics where clerk_org_id=current_setting('app.clerk_org_id',true))"),{'id':workflow_id})).mappings().first()
        if not row: raise HTTPException(status_code=404,detail='workflow not found')
        return dict(row)
    async def activate(self,workflow_id:str):
        current=await self.get(workflow_id)
        if current['status']=='archived': raise HTTPException(status_code=409,detail='archived workflow cannot be activated')
        await self.session.execute(text("update workflows set status='active',updated_at=now() where id=:id and clinic_id in (select id from clinics where clerk_org_id=current_setting('app.clerk_org_id',true))"),{'id':workflow_id}); return await self.get(workflow_id)
    async def trigger(self,organization_id:str,user_id:str,workflow_id:str,trigger_type:str,idempotency_key:str,context:dict[str,Any],request_id:str|None):
        clinic=await self.clinic_id(organization_id); workflow=await self.get(workflow_id)
        if workflow['status']!='active': raise HTTPException(status_code=409,detail='workflow is not active')
        version=(await self.session.execute(text('select id,version,definition from workflow_versions where workflow_id=:id order by version desc limit 1'),{'id':workflow_id})).mappings().first()
        if not version: raise HTTPException(status_code=409,detail='workflow has no version')
        existing=(await self.session.execute(text('select * from workflow_runs where workflow_id=:workflow and clinic_id=:clinic and idempotency_key=:key'),{'workflow':workflow_id,'clinic':clinic,'key':idempotency_key})).mappings().first()
        if existing:return dict(existing)
        steps=(version['definition'] or {}).get('steps',[])
        run_id=str(uuid.uuid4()); await self.session.execute(text("insert into workflow_runs(id,clinic_id,workflow_id,workflow_version_id,status,trigger_type,actor_id,request_id,idempotency_key,context) values(:id,:clinic,:workflow,:version,'queued',:trigger,:actor,:request,:key,cast(:context as jsonb))"),{'id':run_id,'clinic':clinic,'workflow':workflow_id,'version':version['id'],'trigger':trigger_type,'actor':user_id,'request':request_id,'key':idempotency_key,'context':json.dumps(context)})
        for ordinal,step in enumerate(steps):
            await self.session.execute(text("insert into workflow_step_runs(workflow_run_id,step_key,ordinal,input) values(:run,:key,:ordinal,cast(:input as jsonb))"),{'run':run_id,'key':step['key'],'ordinal':ordinal,'input':json.dumps(step.get('input',{}))})
        await self.session.execute(text("insert into workflow_events(id,clinic_id,workflow_run_id,event_type,actor_id,request_id,aggregate_type,aggregate_id) values(:id,:clinic,:run,'workflow.run.created',:actor,:request,'workflow_run',:run)"),{'id':str(uuid.uuid4()),'clinic':clinic,'run':run_id,'actor':user_id,'request':request_id}); return dict((await self.session.execute(text('select * from workflow_runs where id=:id'),{'id':run_id})).mappings().first())
    async def transition(self,organization_id:str,run_id:str,target:str):
        clinic=await self.clinic_id(organization_id); row=(await self.session.execute(text('select status from workflow_runs where id=:id and clinic_id=:clinic for update'),{'id':run_id,'clinic':clinic})).mappings().first()
        if not row: raise HTTPException(status_code=404,detail='workflow run not found')
        if target not in LEGAL_RUN_TRANSITIONS.get(row['status'],set()): raise HTTPException(status_code=409,detail='invalid workflow run state transition')
        terminal=target in {'completed','failed','escalated','cancelled'}
        await self.session.execute(text("update workflow_runs set status=:target,started_at=case when :target='running' and started_at is null then now() else started_at end,completed_at=case when :terminal then now() else completed_at end,updated_at=now() where id=:id and clinic_id=:clinic"),{'target':target,'terminal':terminal,'id':run_id,'clinic':clinic}); return dict((await self.session.execute(text('select * from workflow_runs where id=:id'),{'id':run_id})).mappings().first())
