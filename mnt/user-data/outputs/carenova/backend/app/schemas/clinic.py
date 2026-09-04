"""Clinic schemas."""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class ClinicResponse(BaseModel):
    id: str
    name: str
    clerk_org_id: str
    ehr_type: str
    plan_tier: str
    active_agents: List[str]
    hipaa_baa_signed: bool
    country: str
    created_at: datetime

class ClinicUpdate(BaseModel):
    name: Optional[str] = None
    ehr_type: Optional[str] = None
    ehr_practice_id: Optional[str] = None
    phone_number: Optional[str] = None
    timezone: Optional[str] = None
