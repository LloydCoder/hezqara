from datetime import datetime
from pydantic import BaseModel, Field
class AppointmentCreate(BaseModel):
    patient_id: str
    starts_at: datetime
    ends_at: datetime
    appointment_type: str = Field(min_length=1, max_length=100)
class AppointmentRead(AppointmentCreate):
    id: str
    status: str
