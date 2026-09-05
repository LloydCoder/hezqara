from datetime import date, datetime
from pydantic import BaseModel, ConfigDict, Field

class PatientCreate(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    date_of_birth: date | None = None
    phone: str | None = Field(default=None, max_length=30)
    email: str | None = Field(default=None, max_length=320)
    insurance_carrier: str | None = Field(default=None, max_length=150)
    insurance_member_id: str | None = Field(default=None, max_length=100)

class PatientUpdate(BaseModel):
    first_name: str | None = Field(default=None, min_length=1, max_length=100)
    last_name: str | None = Field(default=None, min_length=1, max_length=100)
    date_of_birth: date | None = None
    phone: str | None = Field(default=None, max_length=30)
    email: str | None = Field(default=None, max_length=320)
    insurance_carrier: str | None = Field(default=None, max_length=150)
    insurance_member_id: str | None = Field(default=None, max_length=100)

class PatientRead(PatientCreate):
    model_config = ConfigDict(from_attributes=True)
    id: str
    created_at: datetime | None = None
    updated_at: datetime | None = None
