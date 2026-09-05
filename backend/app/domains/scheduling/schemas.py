from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

class AppointmentCreate(BaseModel):
    patient_id: str
    appointment_datetime: datetime
    duration_minutes: int = Field(default=20, ge=5, le=480)
    reason: str | None = Field(default=None, max_length=500)
    appointment_type: str = Field(default="general", min_length=1, max_length=100)

class AppointmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    patient_id: str
    appointment_datetime: datetime
    duration_minutes: int
    reason: str | None
    appointment_type: str
    status: str
    created_at: datetime | None = None
    updated_at: datetime | None = None
