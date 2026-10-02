from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field

RequestType = Literal["new_patient","appointment","intake","registration","access_question"]
RequestChannel = Literal["staff","patient_portal","phone","sms","email","agent","api"]
RequestStatus = Literal["new","in_progress","ready","escalated","completed","cancelled"]
SlotStatus = Literal["free","busy","busy-unavailable","busy-tentative","entered-in-error"]

class AccessRequestCreate(BaseModel):
    patient_id: str | None = None
    request_type: RequestType
    channel: RequestChannel = "staff"
    reason: str | None = Field(default=None, max_length=2000)
    requested_start: datetime | None = None
    requested_end: datetime | None = None
    idempotency_key: str = Field(min_length=8, max_length=200)

class AccessRequestUpdate(BaseModel):
    status: RequestStatus

class IntakeSubmissionCreate(BaseModel):
    patient_id: str
    access_request_id: str | None = None
    form_version: str = Field(min_length=1, max_length=100)
    responses: dict = Field(default_factory=dict)
    submit: bool = False

class ScheduleCreate(BaseModel):
    provider_id: str = Field(min_length=1, max_length=200)
    service_type: str | None = Field(default=None, max_length=200)
    specialty: str | None = Field(default=None, max_length=200)
    timezone: str = Field(default="America/New_York", min_length=1, max_length=100)
    planning_start: datetime | None = None
    planning_end: datetime | None = None

class SlotCreate(BaseModel):
    starts_at: datetime
    ends_at: datetime
    status: SlotStatus = "free"
    comment: str | None = Field(default=None, max_length=1000)

class WaitlistCreate(BaseModel):
    patient_id: str
    provider_id: str | None = Field(default=None, max_length=200)
    service_type: str | None = Field(default=None, max_length=200)
    requested_start: datetime | None = None
    requested_end: datetime | None = None
    priority: int = Field(default=100, ge=0)
    notification_channel: Literal["sms","email","phone","portal","none"] = "sms"
    idempotency_key: str = Field(min_length=8, max_length=200)

class BookSlotRequest(BaseModel):
    patient_id: str
    reason: str | None = Field(default=None, max_length=500)
    idempotency_key: str = Field(min_length=8, max_length=200)

class RescheduleRequest(BaseModel):
    new_slot_id: str
    idempotency_key: str = Field(min_length=8, max_length=200)

class CancelAppointmentRequest(BaseModel):
    idempotency_key: str = Field(min_length=8, max_length=200)
    reason: str | None = Field(default=None, max_length=500)
