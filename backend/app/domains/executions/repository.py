from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

class ExecutionRepository:
    def __init__(self,session:AsyncSession): self.session=session
    async def get_by_key(self,agent_type:str,request_key:str):
        result=await self.session.execute(text("select id,actor_id,agent_type,request_key,status,provider,model,confidence,escalation_required,input_summary,result_summary,error_class,started_at,completed_at,created_at,updated_at from agent_executions where agent_type=:agent_type and request_key=:request_key"),{'agent_type':agent_type,'request_key':request_key})
        row=result.mappings().first(); return dict(row) if row else None
    async def create(self,agent_type:str,actor_id:str,request_key:str,input_summary:str):
        result=await self.session.execute(text("""insert into agent_executions (clinic_id,actor_id,agent_type,request_key,status,input_summary)
          select c.id,:actor_id,:agent_type,:request_key,'queued',:input_summary from clinics c where c.clerk_org_id=current_setting('app.clerk_org_id',true)
          returning id,actor_id,agent_type,request_key,status,provider,model,confidence,escalation_required,input_summary,result_summary,error_class,started_at,completed_at,created_at,updated_at"""),{'actor_id':actor_id,'agent_type':agent_type,'request_key':request_key,'input_summary':input_summary[:500]})
        row=result.mappings().first()
        if not row: raise ValueError('organization clinic is not provisioned')
        return dict(row)
    async def mark_running(self,execution_id:str):
        await self.session.execute(text("update agent_executions set status='running',started_at=now(),updated_at=now() where id=:id and status='queued'"),{'id':execution_id})
    async def complete(self,execution_id:str,status:str,provider:str|None,model:str|None,confidence:float|None,escalated:bool,result_summary:str|None,error_class:str|None):
        await self.session.execute(text("""update agent_executions set status=:status,provider=:provider,model=:model,confidence=:confidence,escalation_required=:escalated,result_summary=:result_summary,error_class=:error_class,completed_at=now(),updated_at=now() where id=:id"""),{'id':execution_id,'status':status,'provider':provider,'model':model,'confidence':confidence,'escalated':escalated,'result_summary':result_summary[:1000] if result_summary else None,'error_class':error_class})
