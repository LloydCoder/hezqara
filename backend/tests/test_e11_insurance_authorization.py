import pytest
from datetime import date, datetime, timezone
from app.api.v1.insurance_authorization import ALLOWED
from app.domains.insurance.fhir import coverage_resource, eligibility_request_resource, eligibility_response_resource, authorization_task_resource

def test_authorization_state_machine_is_explicit():
    assert "ready_for_review" in ALLOWED["draft"]
    assert "submitted" in ALLOWED["approved_for_submission"]
    assert "approved" in ALLOWED["pending"]
    assert ALLOWED["denied"] == set()

def test_authorization_submission_is_not_direct_from_draft():
    assert "submitted" not in ALLOWED["draft"]

def test_coverage_fhir_mapping():
    resource=coverage_resource({
        "id":"cov1","patient_id":"p1","payer_name":"Payer","plan_name":"Gold",
        "member_id":"M1","priority":1,"status":"active",
        "effective_date":date(2026,1,1),"termination_date":None
    })
    assert resource["resourceType"]=="Coverage"
    assert resource["beneficiary"]["reference"]=="Patient/p1"
    assert resource["subscriberId"]=="M1"

def test_eligibility_fhir_mapping():
    row={"id":"er1","patient_id":"p1","coverage_id":"cov1","payer_name":"Payer",
         "status":"eligible","requested_at":datetime(2026,1,1,tzinfo=timezone.utc)}
    req=eligibility_request_resource(row)
    resp=eligibility_response_resource(row)
    assert req["resourceType"]=="CoverageEligibilityRequest"
    assert resp["resourceType"]=="CoverageEligibilityResponse"
    assert resp["outcome"]=="complete"

def test_authorization_task_mapping():
    resource=authorization_task_resource({
        "id":"a1","patient_id":"p1","status":"approved_for_submission",
        "created_at":datetime(2026,1,1,tzinfo=timezone.utc)
    })
    assert resource["resourceType"]=="Task"
    assert resource["status"]=="ready"
