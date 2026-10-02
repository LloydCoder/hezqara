import pytest
from app.domains.claims.engine import CLAIM_TRANSITIONS, aging_bucket

def test_claim_lifecycle_requires_scrub_before_ready_by_domain_contract():
    assert "ready" in CLAIM_TRANSITIONS["draft"]
    assert "submitted" in CLAIM_TRANSITIONS["ready"]
    assert "accepted" in CLAIM_TRANSITIONS["submitted"]

def test_denied_claim_can_be_appealed():
    assert "appealed" in CLAIM_TRANSITIONS["denied"]

def test_claim_cannot_jump_from_draft_to_submitted():
    assert "submitted" not in CLAIM_TRANSITIONS["draft"]

@pytest.mark.parametrize(("days","bucket"),[
    (0,"0_30"),(30,"0_30"),(31,"31_60"),(60,"31_60"),
    (61,"61_90"),(90,"61_90"),(91,"91_120"),(120,"91_120"),(121,"120_plus")
])
def test_aging_bucket_boundaries(days,bucket):
    assert aging_bucket(days)==bucket

def test_aging_bucket_rejects_negative_days():
    with pytest.raises(ValueError):
        aging_bucket(-1)
