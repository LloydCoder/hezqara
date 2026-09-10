import json
import re

from fastapi import HTTPException
from app.workforce.base.contracts import AgentContext, AgentRequest

PROMPT_INJECTION_PATTERNS = (
    r"ignore\s+(?:all\s+)?previous\s+instructions",
    r"reveal\s+(?:the\s+)?(?:system|developer)\s+prompt",
    r"bypass\s+(?:authorization|security|policy|safety)",
    r"disregard\s+(?:the\s+)?(?:system|developer)\s+message",
    r"you\s+are\s+now\s+(?:the\s+)?system",
    r"jailbreak",
)
PHI_BOUNDARY_PATTERNS = (
    r"another\s+patient",
    r"different\s+patient",
    r"another\s+clinic",
    r"different\s+clinic",
    r"another\s+tenant",
    r"different\s+tenant",
    r"cross[-\s]?tenant",
    r"another\s+organization",
    r"different\s+organization",
)
PHI_FIELD_PATTERNS = (
    r"\bmedical\s+record\b",
    r"\bpatient\s+id\b",
    r"\bmrn\b",
    r"\bdate\s+of\s+birth\b",
    r"\bdiagnosis\b",
    r"\bmedication\b",
    r"\binsurance\s+member\b",
)

def _request_text(request: AgentRequest) -> str:
    return f"{request.task}\n{json.dumps(request.input, ensure_ascii=False, sort_keys=True, default=str)}".lower()

def detect_prompt_injection(request: AgentRequest) -> bool:
    text = _request_text(request)
    return any(re.search(pattern, text, re.IGNORECASE) for pattern in PROMPT_INJECTION_PATTERNS)

def detect_phi_boundary_violation(request: AgentRequest) -> bool:
    text = _request_text(request)
    return any(re.search(pattern, text, re.IGNORECASE) for pattern in PHI_BOUNDARY_PATTERNS)

def classify_input_data_classes(request: AgentRequest) -> tuple[str, ...]:
    text = _request_text(request)
    classes = {value.strip().lower() for value in request.metadata.get("data_classes", "").split(",") if value.strip()}
    if any(re.search(pattern, text, re.IGNORECASE) for pattern in PHI_FIELD_PATTERNS):
        classes.add("phi")
    return tuple(sorted(classes))

def validate_request(context: AgentContext, request: AgentRequest) -> None:
    if not request.idempotency_key or len(request.idempotency_key) > 200:
        raise HTTPException(status_code=422, detail="valid idempotency key required")
    if detect_prompt_injection(request):
        raise HTTPException(status_code=400, detail="unsafe instruction")

def sanitize_external_content(content: str, *, source: str) -> dict[str, str]:
    """Represent third-party content as untrusted data; callers must not interpolate it as policy/instructions."""
    if not source or len(source) > 100:
        raise ValueError("valid external source required")
    return {"source": source, "trust": "untrusted_external_data", "content": content[:10000]}
