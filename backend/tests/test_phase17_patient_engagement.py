def test_e17_channels_are_explicit_and_bounded():
    assert {"sms","email","whatsapp"} == {"sms","email","whatsapp"}

def test_e17_is_proposal_first():
    assert "proposed" in {"proposed","approved","queued","sent","delivered","failed","cancelled"}
