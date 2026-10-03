from app.domains.documentation_intelligence.service import analyze_note, extract_follow_up, build_quality_summary

def test_missing_sections_are_deterministically_detected():
    findings = analyze_note("Chief complaint: cough")
    keys = {f.key for f in findings}
    assert "missing_history" in keys
    assert "missing_assessment" in keys
    assert "missing_plan" in keys

def test_follow_up_is_explicitly_proposed_not_executed():
    findings = extract_follow_up("Plan: return in 2 weeks for follow-up.")
    assert findings and findings[0].kind == "follow_up"
    assert findings[0].severity == "info"

def test_quality_summary_is_bounded():
    summary = build_quality_summary(analyze_note("Chief complaint: cough"))
    assert 0 <= summary["score"] <= 1
    assert summary["warning_count"] >= 1
