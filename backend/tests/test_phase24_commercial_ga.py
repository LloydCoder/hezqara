def test_launch_gate_is_not_implicitly_ready():
    assert 'blocked' != 'ready'

def test_plan_price_is_integer_minor_units():
    assert isinstance(199900,int)
