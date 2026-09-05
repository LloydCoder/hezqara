from fastapi import APIRouter,Depends,HTTPException,Query,Request
from app.domains.tasks.repository import TaskRepository
from app.domains.tasks.schemas import TaskCreate,TaskUpdate
from app.domains.tasks.service import TaskService
from app.infrastructure.database import tenant_session_context
from app.security.authorization import require_permission
from app.security.tenant import TenantContext
from app.security.audit import append_event
router=APIRouter(prefix='/tasks',tags=['tasks'])
@router.get('')
async def list_tasks(status:str|None=Query(None),limit:int=Query(50,ge=1,le=100),offset:int=Query(0,ge=0),tenant:TenantContext=Depends(require_permission('tasks:read'))):
    async with tenant_session_context(tenant.organization_id) as session:return await TaskService(TaskRepository(session)).list(limit,offset,status)
@router.post('',status_code=201)
async def create_task(data:TaskCreate,request:Request,tenant:TenantContext=Depends(require_permission('tasks:write'))):
    async with tenant_session_context(tenant.organization_id) as session:
        task=await TaskService(TaskRepository(session)).create(data)
        await append_event(session,organization_id=tenant.organization_id,actor=tenant.user_id,action='task.created',resource_type='task',resource_id=task['id'],outcome='success',request_id=getattr(request.state,'request_id',None))
        return task
@router.get('/{task_id}')
async def get_task(task_id:str,tenant:TenantContext=Depends(require_permission('tasks:read'))):
    async with tenant_session_context(tenant.organization_id) as session:
        task=await TaskService(TaskRepository(session)).get(task_id)
        if not task:raise HTTPException(status_code=404,detail='task not found')
        return task
@router.patch('/{task_id}')
async def update_task(task_id:str,data:TaskUpdate,request:Request,tenant:TenantContext=Depends(require_permission('tasks:write'))):
    async with tenant_session_context(tenant.organization_id) as session:
        task=await TaskService(TaskRepository(session)).update(task_id,data)
        await append_event(session,organization_id=tenant.organization_id,actor=tenant.user_id,action='task.updated',resource_type='task',resource_id=task_id,outcome='success',request_id=getattr(request.state,'request_id',None),metadata={'status_changed':data.status is not None,'assignment_changed':data.owner_id is not None})
        return task
