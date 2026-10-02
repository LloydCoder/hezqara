import pytest
from datetime import datetime, timezone
from app.domains.patient_access.schemas import (
    AccessRequestCreate, AccessRequestUpdate, SlotCreate, BookSlotRequest,
    RescheduleRequest, CancelAppointmentRequest,
)
from app.domains.patient_access.service import PatientAccessService
from app.domains.patient_access.fhir import schedule_resource, slot_resource, appointment_resource

class FakeRepository:
    def __init__(self):
        self.rows=[{"id":"r1","status":"new"}]
    async def list_access_requests(self, clinic_id, limit, offset):
        return self.rows
    async def update_access_request(self, clinic_id, request_id, status):
        self.rows[0]["status"]=status
        return self.rows[0]

@pytest.mark.asyncio
async def test_access_request_state_machine():
    row=await PatientAccessService(FakeRepository()).update_access_request("clinic","r1","in_progress")
    assert row["status"]=="in_progress"

@pytest.mark.asyncio
async def test_access_request_rejects_invalid_transition():
    repo=FakeRepository(); repo.rows[0]["status"]="completed"
    with pytest.raises(Exception, match="invalid access request state transition"):
        await PatientAccessService(repo).update_access_request("clinic","r1","new")

def test_idempotency_keys_are_required():
    with pytest.raises(ValueError):
        AccessRequestCreate(request_type="appointment", idempotency_key="short")
    with pytest.raises(ValueError):
        BookSlotRequest(patient_id="p1", idempotency_key="short")
    with pytest.raises(ValueError):
        RescheduleRequest(new_slot_id="s1", idempotency_key="short")
    with pytest.raises(ValueError):
        CancelAppointmentRequest(idempotency_key="short")

def test_slot_requires_valid_window_at_api_boundary():
    slot=SlotCreate.model_validate({"starts_at":"2031-01-01T10:00:00Z","ends_at":"2031-01-01T10:30:00Z"})
    assert slot.ends_at > slot.starts_at

def test_fhir_schedule_mapping():
    row={"id":"s1","provider_id":"prov1","active":True,"service_type":"Consult","specialty":"Primary Care",
         "planning_start":datetime(2031,1,1,9,tzinfo=timezone.utc),"planning_end":datetime(2031,1,1,17,tzinfo=timezone.utc)}
    resource=schedule_resource(row)
    assert resource["resourceType"]=="Schedule"
    assert resource["actor"][0]["reference"]=="Practitioner/prov1"

def test_fhir_slot_mapping():
    row={"id":"sl1","schedule_id":"s1","status":"free","starts_at":datetime(2031,1,1,10,tzinfo=timezone.utc),
         "ends_at":datetime(2031,1,1,10,30,tzinfo=timezone.utc),"overbooked":False,"comment":None}
    resource=slot_resource(row)
    assert resource["resourceType"]=="Slot"
    assert resource["status"]=="free"
    assert resource["schedule"]["reference"]=="Schedule/s1"

def test_fhir_appointment_mapping():
    row={"id":"a1","patient_id":"p1","provider_id":"prov1","status":"scheduled",
         "appointment_datetime":datetime(2031,1,1,10,tzinfo=timezone.utc),"duration_minutes":30,
         "slot_id":"sl1","reason":"follow-up"}
    resource=appointment_resource(row)
    assert resource["resourceType"]=="Appointment"
    assert resource["status"]=="booked"
    assert resource["slot"][0]["reference"]=="Slot/sl1"
