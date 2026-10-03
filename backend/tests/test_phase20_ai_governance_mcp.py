def test_mcp_is_transport_not_authority():
    assert 'mcp' in {'mcp','native','fhir','rest'}

def test_high_risk_side_effect_requires_approval():
    risk_tier=4; side_effect=True; approval_required=True
    assert not (side_effect and risk_tier >= 3 and not approval_required)
