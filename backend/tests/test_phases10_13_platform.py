from decimal import Decimal
import pytest
from app.platform.commercial import PLAN_CATALOG, get_plan
from app.platform.growth import ONBOARDING_STEPS

def test_plan_catalog_has_bounded_production_tiers():
    assert set(PLAN_CATALOG) == {"starter", "growth", "professional", "enterprise"}
    assert PLAN_CATALOG["starter"]["monthly_price_usd"] == Decimal("299.00")
    assert PLAN_CATALOG["enterprise"]["monthly_executions"] > PLAN_CATALOG["professional"]["monthly_executions"]

def test_unknown_plan_is_rejected():
    with pytest.raises(ValueError):
        get_plan("not-a-plan")

def test_onboarding_steps_are_stable():
    assert ONBOARDING_STEPS[0] == "clinic_profile"
    assert "first_workflow" in ONBOARDING_STEPS
