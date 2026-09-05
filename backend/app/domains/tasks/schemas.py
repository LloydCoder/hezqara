from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field

TaskStatus = Literal['open','in_progress','waiting','completed','cancelled','escalated']
TaskPriority = Literal['low','normal','high','urgent']

class TaskCreate(BaseModel):
    title: str = Field(min_length=1,max_length=200)
    description: str | None = Field(default=None,max_length=2000)
    priority: TaskPriority = 'normal'
    owner_id: str | None = None
    patient_id: str | None = None
    agent_type: str | None = Field(default=None,max_length=100)
    due_at: datetime | None = None

class TaskUpdate(BaseModel):
    status: TaskStatus | None = None
    priority: TaskPriority | None = None
    owner_id: str | None = None
    due_at: datetime | None = None
    description: str | None = Field(default=None,max_length=2000)

class TaskRead(BaseModel):
    id: str
    title: str
    description: str | None
    status: TaskStatus
    priority: TaskPriority
    owner_id: str | None
    source: str
    patient_id: str | None
    agent_type: str | None
    due_at: datetime | None
    escalation_reason: str | None
    created_at: datetime
    updated_at: datetime
