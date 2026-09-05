import pytest
from app.domains.claims.engine import aging_bucket, validate_claim_transition, validate_payment_state
from app.ai.administrative import classify_denial
from app.integrations.fhir import FHIRAdapter

def test_claim_lifecycle_rejects_skip():
    validate_claim_transition('draft','ready')
    with pytest.raises(ValueError): validate_claim_transition('draft','paid')

def test_payment_states_are_bounded():
    validate_payment_state('paid')
    with pytest.raises(ValueError): validate_payment_state('captured')

def test_aging_buckets():
    assert aging_bucket(0)=='0_30'; assert aging_bucket(31)=='31_60'; assert aging_bucket(121)=='120_plus'

def test_denial_classifier_is_structured_and_reviewable():
    result=classify_denial('Missing information for claim', 'exec-1')
    assert result.classification=='missing_information'; assert result.requires_human_review is True; assert 0 <= result.confidence <= 1

def test_fhir_boundary_rejects_wrong_resource():
    with pytest.raises(ValueError): FHIRAdapter.coverage({'resourceType':'Patient'})
