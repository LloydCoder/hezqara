from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field

Channel = Literal['sms','email','whatsapp']
CommunicationStatus = Literal['draft','queued','sending','sent','delivered','failed','cancelled','blocked']

class CommunicationCreate(BaseModel):
    patient_id: str
    appointment_id: str | None = None
    workflow_run_id: str | None = None
    channel: Channel
    body: str = Field(min_length=1,max_length=10000)
    subject: str | None = Field(default=None,max_length=200)
    template_key: str | None = Field(default=None,max_length=100)
    idempotency_key: str = Field(min_length=8,max_length=200)

class CommunicationRead(BaseModel):
    id: str; patient_id: str; appointment_id: str | None; workflow_run_id: str | None
    channel: Channel; direction: Literal['inbound','outbound']; status: CommunicationStatus
    subject: str | None; body: str; template_key: str | None; provider_reference: str | None
    failure_class: str | None; idempotency_key: str; correlation_id: str | None
    created_at: datetime; updated_at: datetime; sent_at: datetime | None; delivered_at: datetime | None

class CommunicationPreferenceUpdate(BaseModel):
    sms_enabled: bool = True
    email_enabled: bool = True
    whatsapp_enabled: bool = False
    opted_out_all: bool = False
    timezone: str = Field(default='UTC',min_length=1,max_length=100)

class MessageIntake(BaseModel):
    patient_id: str
    channel: Channel
    message: str = Field(min_length=1,max_length=10000)
    appointment_id: str | None = None

class MessageClassification(BaseModel):
    intent: Literal['appointment_confirmation','reschedule','cancel','no_show','billing','clinical','general','unknown']
    urgency: Literal['low','normal','high','emergency']
    requires_human: bool
    safe_to_draft: bool
    reason: str = Field(max_length=500)
