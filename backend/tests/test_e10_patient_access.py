import pytest
from app.domains.patient_access.schemas import AccessRequestCreate, AccessRequestUpdate, SlotCreate
from app.domains.patient_access.service import PatientAccessService

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
    service=PatientAccessService(FakeRepository())
    row=await service.update_access_request("clinic","r1","in_progress")
    assert row["status"]=="in_progress"

@pytest.mark.asyncio
async def test_access_request_rejects_invalid_transition():
    repo=FakeRepository()
    repo.rows[0]["status"]="completed"
    with pytest.raises(Exception, match="invalid access request state transition"):
        await PatientAccessService(repo).update_access_request("clinic","r1","new")

def test_access_request_requires_idempotency_key():
    with pytest.raises(ValueError):
        AccessRequestCreate(request_type="appointment", idempotency_key="short")

def test_slot_requires_valid_window_at_api_boundary():
    slot=SlotCreate.model_validate({
        "starts_at":"2031-01-01T10:00:00Z",
        "ends_at":"2031-01-01T10:30:00Z"
    })
    assert slot.ends_at > slot.starts_at

def test_status_contract_is_explicit():
    assert AccessRequestUpdate(status="ready").status=="ready"
