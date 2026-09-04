"""
WhatsApp Template Service.

Meta's pricing/policy rules (verified against current WhatsApp Business
Platform documentation):
  - Messages sent within 24h of the patient's last message: free-form,
    no template required, no charge.
  - Messages sent outside that window: must use a pre-approved template.
    Utility category (transactional — appointment reminders, order
    updates) is far cheaper and more reliable than marketing category.
  - Using free-form text outside the window gets the message blocked,
    not billed — so this is a hard functional requirement, not just cost.

Carenova's walk-in flow is mostly inbound-driven (patient scans QR,
messages first), which keeps the "queue called" notification inside the
free window in the common case. But follow-up reminders sent days later
are always outside the window and MUST use a template.
"""
import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


# Pre-registered template bodies, matching app/walkin/messages.py content
# but in Meta's {{1}}, {{2}} placeholder format required for template submission.
TEMPLATE_REGISTRY = {
    "queue_called": {
        "category": "utility",
        "bodies": {
            "en": "It's your turn! Please come to {{1}} to see {{2}} now.",
            "ig": "Oge gị eruola! Biko bia na {{1}} ịhụ {{2}} ugbu a.",
            "yo": "Àkókò rẹ ti dé! Jọwọ wá sí {{1}} láti rí {{2}} báyìí.",
            "ha": "Lokacin ka ya zo! Don Allah zo {{1}} don ganin {{2}} yanzu.",
            "fr": "C'est votre tour! Veuillez vous rendre à {{1}} pour voir {{2}} maintenant.",
            "sw": "Ni zamu yako! Tafadhali nenda {{1}} kuona {{2}} sasa.",
            "hi": "आपकी बारी आ गई! कृपया अभी {{1}} में {{2}} से मिलें।",
            "fil": "Ang inyong turn na! Mangyaring pumunta sa {{1}} para makita si {{2}} ngayon.",
        },
    },
    "followup_reminder": {
        "category": "utility",
        "bodies": {
            "en": "Hello {{1}}! This is a reminder from {{2}}. Your follow-up visit is recommended in {{3}} days.",
            "ig": "Ndewo {{1}}! Nke a bụ ncheta si {{2}}. A na-atụ aro ka ị laghachi n'ime {{3}} ụbọchị.",
            "yo": "Ẹ káàárọ̀ {{1}}! Ìránṣẹ́ àkọsílẹ̀ láti {{2}}. A gbani lára pé kí ọ padà wá ní {{3}} ọjọ́.",
            "ha": "Sannu {{1}}! Wannan tuno ne daga {{2}}. An ba da shawarar ziyara a cikin kwana {{3}}.",
            "fr": "Bonjour {{1}}! Ceci est un rappel de {{2}}. Une visite de suivi est recommandée dans {{3}} jours.",
            "sw": "Habari {{1}}! Hii ni ukumbusho kutoka {{2}}. Ziara ya ufuatiliaji inapendekezwa siku {{3}}.",
            "hi": "नमस्ते {{1}}! यह {{2}} से अनुस्मारक है। {{3}} दिनों में फॉलो-अप विज़िट की सलाह दी गई है।",
            "fil": "Kamusta {{1}}! Paalala mula sa {{2}}. Inirerekomenda ang follow-up sa loob ng {{3}} araw.",
        },
    },
    "appointment_confirmation": {
        "category": "utility",
        "bodies": {
            "en": "Your appointment at {{1}} is confirmed for {{2}} with {{3}}.",
            "fr": "Votre rendez-vous à {{1}} est confirmé pour {{2}} avec {{3}}.",
        },
    },
}


class WhatsAppTemplateService:
    """
    Manages WhatsApp utility templates and decides when free-form text
    vs. a pre-approved template must be used.
    """

    def __init__(self) -> None:
        self._registered: dict = {}

    def register_template(
        self,
        template_name: str,
        language: str,
        category: str,
        body_text: str,
    ) -> dict:
        """
        Register a template for Meta submission.
        In production: calls the WhatsApp Business Management API to
        submit for approval. Here: tracks local state + DB record shape.
        """
        key = f"{template_name}:{language}"
        record = {
            "template_name": template_name,
            "language": language,
            "category": category,
            "body_text": body_text,
            "approval_status": "pending",
            "submitted_at": datetime.utcnow().isoformat(),
        }
        self._registered[key] = record
        logger.info("WhatsApp template registered for submission: %s", key)
        return record

    def get_template_for(self, template_name: str, language: str = "en") -> dict:
        """Get the registered template body for a purpose + language."""
        entry = TEMPLATE_REGISTRY.get(template_name)
        if not entry:
            raise ValueError(f"Unknown template: {template_name}")

        body = entry["bodies"].get(language, entry["bodies"]["en"])
        return {
            "template_name": template_name,
            "language": language,
            "category": entry["category"],
            "body_text": body,
        }

    def get_all_templates(self) -> list:
        """All templates that must be submitted to Meta for approval."""
        templates = []
        for name, entry in TEMPLATE_REGISTRY.items():
            for lang, body in entry["bodies"].items():
                templates.append({
                    "template_name": name,
                    "language": lang,
                    "category": entry["category"],
                    "body_text": body,
                })
        return templates

    def decide_message_type(
        self,
        last_patient_message_hours_ago: Optional[float],
        message_purpose: str,
    ) -> dict:
        """
        Decide whether to send free-form text or a pre-approved template.

        Rule: if the patient messaged within the last 24 hours, the
        service window is open and free-form text works and is free.
        Otherwise a template is required.
        """
        within_window = (
            last_patient_message_hours_ago is not None
            and last_patient_message_hours_ago < 24
        )

        if within_window:
            return {
                "use_template": False,
                "reason": "within_24h_service_window",
                "message_purpose": message_purpose,
            }

        entry = TEMPLATE_REGISTRY.get(message_purpose, {})
        return {
            "use_template": True,
            "reason": "outside_24h_service_window",
            "template_category": entry.get("category", "utility"),
            "message_purpose": message_purpose,
        }
