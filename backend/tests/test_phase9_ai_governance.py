import pytest
from app.ai.governance.contracts import RiskTier,classify_risk,validate_output,score_case,FAILURE_CATEGORIES

def test_clinical_high_impact_is_never_autonomous():
    d=classify_risk(4,'diagnosis'); assert d.decision=='deny'; assert d.risk_tier==RiskTier.CLINICAL_HIGH_IMPACT

def test_high_impact_requires_approval():
    assert classify_risk(3,'billing_adjustment').decision=='approval_required'

def test_malformed_output_is_rejected():
    ok,reason=validate_output({'action':'x','response':'y','confidence':2,'escalate':False}); assert not ok and reason=='OUTPUT_INVALID'

def test_valid_output_scores():
    out={'action':'schedule','response':'done','confidence':.9,'escalate':False}; s=score_case(out,{'action':'schedule'}); assert s.passed and s.safety_passed and s.score==1

def test_grounding_requires_evidence():
    out={'action':'schedule','response':'done','confidence':.9,'escalate':False}; s=score_case(out,{'action':'schedule','required_evidence':True}); assert not s.passed and s.failure_category=='OUTPUT_UNGROUNDED'

def test_failure_taxonomy_is_canonical():
    assert {'OUTPUT_INVALID','POLICY_DENIED','PROMPT_INJECTION_DETECTED','PHI_BOUNDARY_VIOLATION'}.issubset(FAILURE_CATEGORIES)
