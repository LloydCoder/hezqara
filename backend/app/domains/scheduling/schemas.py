from datetime import datetime
from typing import Literal
from pydantic import BaseModel,ConfigDict,Field
class AppointmentCreate(BaseModel):
    patient_id:str
    appointment_datetime:datetime
    duration_minutes:int=Field(default=20,ge=5,le=480)
    reason:str|None=Field(default=None,max_length=500)
class AppointmentUpdate(BaseModel):
    status:Literal['scheduled','confirmed','completed','cancelled','no_show']|None=None
    reason:str|None=Field(default=None,max_length=500)
class AppointmentRead(BaseModel):
    model_config=ConfigDict(from_attributes=True)
    id:str;patient_id:str;patient_name:str|None;provider_id:str|None;provider_name:str|None;appointment_datetime:datetime;duration_minutes:int;reason:str|None;status:str;created_at:datetime|None=None;updated_at:datetime|None=None
