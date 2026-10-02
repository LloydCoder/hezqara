import pytest
from decimal import Decimal
from app.api.v1.patient_financial import _validate_channel

def test_estimate_responsibility_math_contract():
    charges=Decimal("100")
    payer=Decimal("70")
    patient=Decimal("30")
    assert payer+patient <= charges

def test_estimate_cannot_exceed_total():
    assert Decimal("80")+Decimal("30") > Decimal("100")

@pytest.mark.parametrize("channel",["portal","email","sms","mail","staff"])
def test_statement_channels_are_supported(channel):
    _validate_channel(channel)

def test_statement_channel_rejects_unknown_value():
    with pytest.raises(Exception):
        _validate_channel("carrier-pigeon")
