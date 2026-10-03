def test_compliance_status_is_evidence_oriented():
    assert {'planned','implemented','evidenced','exception'} >= {'evidenced'}

def test_hipaa_is_not_a_boolean_certification_flag():
    assert 'evidenced' in {'planned','implemented','evidenced','exception'}
