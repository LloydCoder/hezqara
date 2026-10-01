from app.platform.reliability import DEFAULT_SLOS

def test_e8_slos_have_explicit_targets():
    assert {x["name"] for x in DEFAULT_SLOS} == {"api_availability","durable_job_success"}
    assert all(0 < x["target"] <= 1 for x in DEFAULT_SLOS)
    assert all(1 <= x["window_days"] <= 365 for x in DEFAULT_SLOS)
