from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

class OperationsRepository:
    def __init__(self,session:AsyncSession): self.session=session
    async def summary(self):
        result=await self.session.execute(text("""select
          (select count(*) from patients) as patients,
          (select count(*) from appointments where appointment_datetime >= date_trunc('day',now())) as appointments_today,
          (select count(*) from tasks where status not in ('completed','cancelled')) as open_tasks,
          (select count(*) from tasks where status='escalated') as escalated_tasks,
          (select count(*) from agent_executions where status in ('queued','running','waiting_for_approval','escalated')) as active_executions,
          (select count(*) from agent_executions where status='completed' and created_at >= now()-interval '24 hours') as completed_executions_24h"""))
        return dict(result.mappings().one())
