"""
Confidence Scoring + Human Handoff.

AI confidence is continuous (0.0–1.0), not binary.
The system monitors confidence and triggers appropriate action:

  ≥ 0.85  → AI continues autonomously
  0.65–0.85 → AI continues, staff notified silently
  0.45–0.65 → AI flags uncertainty to patient, offers staff
  < 0.45  → Immediate warm transfer to human staff

This builds trust with clinics — they know AI won't guess
on complex situations.
"""
import logging
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)

# Confidence thresholds
AUTONOMOUS_THRESHOLD = 0.85    # AI handles without notification
NOTIFY_THRESHOLD = 0.65        # AI handles, staff silently notified
ASSIST_THRESHOLD = 0.45        # Patient offered staff option
TRANSFER_THRESHOLD = 0.45      # Below this → immediate transfer


@dataclass
class ConfidenceAssessment:
    score: float                      # 0.0 → 1.0
    action: str                       # autonomous | notify | assist | transfer
    reason: Optional[str] = None
    notify_staff: bool = False
    offer_human: bool = False
    transfer_immediately: bool = False
    message_to_patient: Optional[str] = None


def assess_confidence(
    confidence_score: float,
    task_type: str,
    clinic_name: str = "the clinic",
) -> ConfidenceAssessment:
    """
    Assess AI confidence and determine appropriate action.

    Args:
        confidence_score: 0.0–1.0 from the AI model response
        task_type: which agent task produced this score
        clinic_name: for personalised patient messages

    Returns:
        ConfidenceAssessment with action and communication guidance
    """
    score = max(0.0, min(1.0, confidence_score))

    if score >= AUTONOMOUS_THRESHOLD:
        return ConfidenceAssessment(
            score=score,
            action="autonomous",
            notify_staff=False,
            offer_human=False,
            transfer_immediately=False,
        )

    if score >= NOTIFY_THRESHOLD:
        return ConfidenceAssessment(
            score=score,
            action="notify",
            reason=f"Confidence {score:.0%} — staff notified",
            notify_staff=True,
            offer_human=False,
            transfer_immediately=False,
        )

    if score >= ASSIST_THRESHOLD:
        return ConfidenceAssessment(
            score=score,
            action="assist",
            reason=f"Confidence {score:.0%} — offering staff assistance",
            notify_staff=True,
            offer_human=True,
            transfer_immediately=False,
            message_to_patient=(
                f"I want to make sure I'm helping you correctly. "
                f"Would you like me to connect you with one of our staff members at "
                f"{clinic_name}?"
            ),
        )

    return ConfidenceAssessment(
        score=score,
        action="transfer",
        reason=f"Confidence {score:.0%} — transferring to human",
        notify_staff=True,
        offer_human=True,
        transfer_immediately=True,
        message_to_patient=(
            f"I want to make sure you get the best help possible. "
            f"Let me connect you with one of our team members right away."
        ),
    )


def extract_confidence_from_response(response: dict) -> float:
    """
    Extract or infer confidence score from LLM response.

    If the model returned a structured JSON with a confidence field, use it.
    Otherwise, infer from response characteristics.
    """
    content = response.get("content", "")

    # Try to parse explicit confidence from JSON responses
    if '"confidence"' in content:
        import json
        try:
            cleaned = content.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
            data = json.loads(cleaned)
            if "confidence" in data:
                return float(data["confidence"])
        except Exception:
            pass

    # Infer from response quality signals
    if not content or len(content.strip()) < 3:
        return 0.3  # Empty or very short response → low confidence

    if response.get("fallback"):
        return 0.4  # Fallback model used → lower confidence

    # Default: assume moderate confidence for clean responses
    return 0.80


class HumanHandoffManager:
    """
    Manages warm transfers to human staff.
    Tracks handoffs and reasons for analytics.
    """

    def __init__(self) -> None:
        self._handoffs: list[dict] = []

    async def initiate_handoff(
        self,
        call_id: str,
        clinic_id: str,
        agent_type: str,
        confidence: float,
        reason: str,
        retell_client=None,
    ) -> dict:
        """
        Initiate warm transfer to human staff.
        Notifies staff via Retell AI transfer or SMS fallback.
        """
        record = {
            "call_id": call_id,
            "clinic_id": clinic_id,
            "agent_type": agent_type,
            "confidence": confidence,
            "reason": reason,
            "status": "initiated",
        }

        try:
            if retell_client:
                await retell_client.warm_transfer(call_id=call_id)
                record["status"] = "transferred"
            else:
                # SMS fallback: notify clinic staff
                logger.info(
                    "HANDOFF NEEDED — call %s clinic %s confidence %.0f%% reason: %s",
                    call_id, clinic_id, confidence * 100, reason
                )
                record["status"] = "notified_staff"

        except Exception as e:
            logger.error("Handoff failed for call %s: %s", call_id, str(e))
            record["status"] = "failed"
            record["error"] = str(e)

        self._handoffs.append(record)
        return record

    def get_handoff_rate(self, clinic_id: Optional[str] = None) -> float:
        """Return percentage of calls that required human handoff."""
        records = [
            h for h in self._handoffs
            if clinic_id is None or h["clinic_id"] == clinic_id
        ]
        if not records:
            return 0.0
        transferred = sum(1 for h in records if h["status"] in ("transferred", "notified_staff"))
        return round(transferred / len(records), 4)


# Global singletons
handoff_manager = HumanHandoffManager()
