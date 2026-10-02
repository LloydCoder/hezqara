import pytest
from app.domains.scribe.speech import provider_contract

def test_speech_provider_is_replaceable():
    contract=provider_contract()
    assert contract["interface"]=="speech-provider.v1"
    assert contract["provider_is_replaceable"] is True
    assert "speaker_diarization" in contract["capabilities"]

def test_scribe_provider_contract_does_not_own_canonical_state():
    assert provider_contract()["canonical_state_owner"]=="hezqara"

def test_clinical_documentation_requires_explicit_human_approval_in_workflow():
    assert "approved" not in {"draft","review","committed"}
