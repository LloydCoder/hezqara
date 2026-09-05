from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.domains.tasks.schemas import TaskCreate, TaskUpdate

class TaskRepository:
    def __init__(self, session: AsyncSession): self.session=session
    async def list(self, limit:int, offset:int, status:str|None=None):
        result=await self.session.execute(text("""select id,title,description,status,priority,owner_id,source,patient_id,agent_type,due_at,escalation_reason,created_at,updated_at
          from tasks where (:status is null or status=:status) order by created_at desc,id desc limit :limit offset :offset"""),{"limit":limit,"offset":offset,"status":status})
        return [dict(r._mapping) for r in result]
    async def get(self, task_id:str):
        result=await self.session.execute(text("select id,title,description,status,priority,owner_id,source,patient_id,agent_type,due_at,escalation_reason,created_at,updated_at from tasks where id=:id"),{"id":task_id})
        row=result.mappings().first(); return dict(row) if row else None
    async def create(self,data:TaskCreate):
        result=await self.session.execute(text("""insert into tasks (clinic_id,title,description,priority,owner_id,patient_id,agent_type,source,due_at)
          select c.id,:title,:description,:priority,:owner_id,
                 case when exists(select 1 from patients p where p.id=:patient_id and p.clinic_id=c.id) then :patient_id else null end,
                 :agent_type,case when :agent_type is null then 'human' else 'agent' end,:due_at
          from clinics c where c.clerk_org_id=current_setting('app.clerk_org_id',true)
          returning id,title,description,status,priority,owner_id,source,patient_id,agent_type,due_at,escalation_reason,created_at,updated_at"""),data.model_dump())
        row=result.mappings().first()
        if not row: raise ValueError('organization clinic is not provisioned')
        return dict(row)
    async def update(self,task_id:str,data:TaskUpdate):
        values=data.model_dump(exclude_unset=True)
        if not values:return await self.get(task_id)
        params={'id':task_id,**values}
        result=await self.session.execute(text("""update tasks set status=coalesce(:status,status),priority=coalesce(:priority,priority),owner_id=coalesce(:owner_id,owner_id),due_at=coalesce(:due_at,due_at),description=coalesce(:description,description),updated_at=now()
          where id=:id returning id,title,description,status,priority,owner_id,source,patient_id,agent_type,due_at,escalation_reason,created_at,updated_at"""),params)
        row=result.mappings().first(); return dict(row) if row else None
