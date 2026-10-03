from dataclasses import dataclass
import re

@dataclass(frozen=True)
class DocumentationFinding:
    kind: str
    key: str
    detail: str
    severity: str
    confidence: float
    source_ref: str | None = None

DEFAULT_SECTIONS = ("chief_complaint", "history", "assessment", "plan")

def analyze_note(note_text: str, *, source_ref: str | None = None) -> list[DocumentationFinding]:
    text = note_text.strip()
    lowered = text.lower()
    findings: list[DocumentationFinding] = []
    if not text:
        return [DocumentationFinding("completeness", "note_empty", "No documentation content is present.", "warning", 1.0, source_ref)]
    section_aliases = {
        "chief_complaint": ("chief complaint", "cc:"),
        "history": ("history", "hpi", "history of present illness"),
        "assessment": ("assessment",),
        "plan": ("plan",),
    }
    for key, aliases in section_aliases.items():
        if not any(alias in lowered for alias in aliases):
            findings.append(DocumentationFinding("completeness", f"missing_{key}", f"Expected {key.replace('_',' ')} section was not detected.", "warning", 0.98, source_ref))
    if re.search(r"\b(todo|follow[- ]?up|return|recheck|schedule)\b", lowered) and not re.search(r"\b(follow[- ]?up|return|recheck|schedule)\b", lowered):
        findings.append(DocumentationFinding("follow_up", "follow_up_ambiguous", "Possible follow-up instruction requires explicit timing or destination.", "info", 0.72, source_ref))
    if re.search(r"\b(maybe|possibly|unclear|unsure|unknown)\b", lowered):
        findings.append(DocumentationFinding("uncertainty", "uncertain_content", "Uncertainty language is present and should remain explicit during review.", "info", 0.95, source_ref))
    return findings

def extract_follow_up(note_text: str) -> list[DocumentationFinding]:
    matches = re.findall(r"(?i).{0,80}\b(?:follow[- ]?up|return|recheck|schedule)\b.{0,120}", note_text)
    return [
        DocumentationFinding("follow_up", "follow_up_instruction", m.strip(), "info", 0.9)
        for m in matches[:10]
    ]

def build_quality_summary(findings: list[DocumentationFinding]) -> dict:
    warnings = sum(1 for f in findings if f.severity == "warning")
    critical = sum(1 for f in findings if f.severity == "critical")
    score = max(0.0, min(1.0, 1.0 - min(1.0, (warnings * 0.15) + (critical * 0.5))))
    return {"score": round(score, 4), "warning_count": warnings, "critical_count": critical, "finding_count": len(findings)}
