"""Patient schemas."""
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import date, datetime

class PatientResponse(BaseModel):
    id: str
    clinic_id: str
    ehr_patient_id: Optional[str] = None
    first_name: str
    last_name: str
    date_of_birth: Optional[date] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    insurance_carrier: Optional[str] = None
    insurance_member_id: Optional[str] = None
    uninsured: bool = False
    created_at: datetime

class PatientCreate(BaseModel):
    first_name: str
    last_name: str
    date_of_birth: Optional[date] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    insurance_carrier: Optional[str] = None
    insurance_member_id: Optional[str] = None
