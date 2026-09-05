import json
import logging
from typing import Any
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
logger=logging.getLogger('hezqara.audit')
_SENSITIVE={'authorization','token','password','secret','api_key','access_token','refresh_token','cookie'}
def sanitize_metadata(metadata:dict[str,Any]|None)->dict[str,Any]:
    clean={}
    for key,value in (metadata or {}).items():
        if any(part in key.lower() for part in _SENSITIVE):continue
        clean[key]=value if isinstance(value,(str,int,float,bool,type(None))) else str(value)[:500]
    return clean
async def append_event(session:AsyncSession,*,organization_id:str,actor:str,action:str,resource_type:str,resource_id:str|None,outcome:str,request_id:str|None=None,metadata:dict[str,Any]|None=None)->None:
    clinic=await session.execute(text('select id from clinics where clerk_org_id=:org_id'),{'org_id':organization_id}); clinic_id=clinic.scalar_one_or_none()
    if not clinic_id:raise ValueError('organization clinic is not provisioned')
    safe=sanitize_metadata(metadata)
    agent_type=safe.get('agent_type') if isinstance(safe.get('agent_type'),str) else None
    await session.execute(text("""insert into audit_log (event_type,clinic_id,actor_id,resource_type,resource_id,request_id,outcome,agent_type,action,metadata,created_at)
      values (:event_type,:clinic_id,:actor_id,:resource_type,:resource_id,:request_id,:outcome,:agent_type,:action,cast(:metadata as jsonb),now())"""),{'event_type':resource_type,'clinic_id':clinic_id,'actor_id':actor,'resource_type':resource_type,'resource_id':resource_id,'request_id':request_id,'outcome':outcome,'agent_type':agent_type,'action':action,'metadata':json.dumps(safe)})
    logger.info('audit action=%s resource=%s outcome=%s request_id=%s',action,resource_type,outcome,request_id)
def record(*,tenant:str,actor:str,action:str,resource:str,resource_id:str|None,outcome:str,request_id:str|None=None,metadata:dict[str,Any]|None=None)->None:
    logger.info('audit actor=%s tenant=%s action=%s resource=%s resource_id=%s outcome=%s request_id=%s metadata=%s',actor,tenant,action,resource,resource_id,outcome,request_id,sanitize_metadata(metadata))
