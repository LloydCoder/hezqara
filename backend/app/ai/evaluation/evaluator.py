from dataclasses import dataclass

@dataclass(frozen=True)
class Evaluation:
    valid: bool
    reasons: tuple[str, ...]

def evaluate_output(output: dict, confidence: float) -> Evaluation:
    reasons=[]
    required={"action","response","confidence","escalate"}
    if not required.issubset(output): reasons.append("missing required fields")
    if not 0.0 <= confidence <= 1.0: reasons.append("confidence outside range")
    if not isinstance(output.get("action"),str) or not output.get("action","").strip(): reasons.append("action must be non-empty")
    if not isinstance(output.get("response"),str): reasons.append("response must be text")
    if not isinstance(output.get("escalate"),bool): reasons.append("escalate must be boolean")
    return Evaluation(not reasons,tuple(reasons))
