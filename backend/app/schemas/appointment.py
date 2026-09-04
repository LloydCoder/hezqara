"""Appointment schemas."""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class AppointmentResponse(BaseModel):
    id: str
    clinic_id: str
    patient_id: str
    patient_name: Optional[str] = None
    ehr_appointment_id: Optional[str] = None
    provider_id: Optional[str] = None
    provider_name: Optional[str] = None
    appointment_datetime: datetime
    duration_minutes: int = 20
    reason: Optional[str] = None
    status: str
    booked_by_agent: str
    call_id: Optional[str] = None
    created_at: datetime

class AppointmentCancelRequest(BaseModel):
    reason: str
