from app.api.v1.documentation_intelligence import TEMPLATES

def test_supported_specialty_templates_are_explicit():
    assert "primary-care" in TEMPLATES
    assert "assessment" in TEMPLATES["primary-care"]
    assert "plan" in TEMPLATES["primary-care"]

def test_unsupported_specialty_is_not_silently_accepted():
    assert "unknown-specialty" not in TEMPLATES
