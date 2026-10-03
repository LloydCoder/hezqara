from app.domains.documentation_intelligence.service import analyze_note, build_quality_summary, extract_follow_up

def test_documentation_analysis_detects_missing_sections():
    findings = analyze_note("Chief Complaint: cough\nHistory: two days")
    keys = {finding.key for finding in findings}
    assert "missing_assessment" in keys
    assert "missing_plan" in keys

def test_follow_up_is_extracted_as_proposal():
    findings = extract_follow_up("Plan: return for follow-up in 2 weeks.")
    assert findings and findings[0].kind == "follow_up"

def test_quality_summary_is_bounded():
    summary = build_quality_summary([])
    assert 0 <= summary["score"] <= 1
