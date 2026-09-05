from fastapi import HTTPException
from app.domains.tasks.repository import TaskRepository
from app.domains.tasks.schemas import TaskCreate, TaskUpdate

_ALLOWED_TRANSITIONS = {
    'open': {'in_progress','waiting','completed','cancelled','escalated'},
    'in_progress': {'open','waiting','completed','cancelled','escalated'},
    'waiting': {'open','in_progress','completed','cancelled','escalated'},
    'completed': set(),
    'cancelled': set(),
    'escalated': {'open','in_progress','completed','cancelled'},
}

class TaskService:
    def __init__(self, repo: TaskRepository): self.repo=repo
    async def list(self,limit:int,offset:int,status:str|None=None): return await self.repo.list(limit,offset,status)
    async def get(self,task_id:str): return await self.repo.get(task_id)
    async def create(self,data:TaskCreate): return await self.repo.create(data)
    async def update(self,task_id:str,data:TaskUpdate):
        current=await self.repo.get(task_id)
        if not current: raise HTTPException(status_code=404,detail='task not found')
        if data.status is not None and data.status != current['status'] and data.status not in _ALLOWED_TRANSITIONS[current['status']]:
            raise HTTPException(status_code=409,detail='invalid task state transition')
        return await self.repo.update(task_id,data)
