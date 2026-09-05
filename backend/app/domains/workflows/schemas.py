from typing import Any, Literal
from pydantic import BaseModel, Field

WorkflowStatus = Literal['draft','active','paused','archived']
RunStatus = Literal['queued','running','waiting_for_approval','completed','failed','escalated','cancelled']

class WorkflowCreate(BaseModel):
    key: str = Field(min_length=2, max_length=100, pattern=r'^[a-z][a-z0-9_-]*$')
    name: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=1000)
    definition: dict[str, Any] = Field(default_factory=dict)

class WorkflowTrigger(BaseModel):
    idempotency_key: str = Field(min_length=8, max_length=200)
    trigger_type: str = Field(min_length=2, max_length=50)
    context: dict[str, Any] = Field(default_factory=dict)
