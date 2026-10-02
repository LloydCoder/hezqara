import pytest
from app.api.v1.document_intelligence import ALLOWED_ROUTE_TARGETS

def test_document_route_targets_are_explicit():
    assert "patient_record" in ALLOWED_ROUTE_TARGETS
    assert "authorization" in ALLOWED_ROUTE_TARGETS
    assert "referral" in ALLOWED_ROUTE_TARGETS
    assert "review_queue" in ALLOWED_ROUTE_TARGETS

def test_unsafe_or_unknown_route_targets_are_not_allowed():
    assert "external_webhook" not in ALLOWED_ROUTE_TARGETS
    assert "autonomous_clinical_decision" not in ALLOWED_ROUTE_TARGETS

@pytest.mark.parametrize("source",["fax","email","upload","ehr","api"])
def test_supported_document_sources(source):
    assert source in {"fax","email","upload","ehr","api"}
