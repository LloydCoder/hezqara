from datetime import date, datetime
from pydantic import BaseModel, ConfigDict, Field

class PatientCreate(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    date_of_birth: date | None = None
    phone: str | None = None
    email: str | None = None
    insurance_carrier: str | None = None
    insurance_member_id: str | None = None

class PatientRead(PatientCreate):
    model_config = ConfigDict(from_attributes=True)
    id: str
    created_at: datetime | None = None
    updated_at: datetime | None = None
