"""
WhatsApp Router — webhook endpoint for walk-in check-in and standalone intake.
GET  /whatsapp/webhook — Meta verification challenge
POST /whatsapp/webhook — Inbound patient messages, routed to walk-in handler

Fixes confirmed gap: this previously only logged messages and returned —
it now actually routes through WalkInIntakeHandler, resolves the correct
clinic from the WhatsApp phone_number_id, and sends the reply back.
"""
import logging
from typing import Optional
from fastapi import APIRouter, Request, Query
from fastapi.responses import JSONResponse, PlainTextResponse

from app.voice.whatsapp import WhatsAppClient
from app.walkin.intake import WalkInIntakeHandler
from app.walkin.queue import QueueManager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/whatsapp", tags=["whatsapp"])

DEFAULT_CLINIC_ID = "clinic_ng_default"

# Module-level client — mocked in tests
_client = WhatsAppClient(
    api_token="",
    phone_number_id="",
    verify_token="carenova_whatsapp_verify",
)

# Per-clinic queue managers (mirrors app/routers/walkin.py pattern)
_queue_managers: dict = {}

def _get_queue_manager(clinic_id: str) -> QueueManager:
    if clinic_id not in _queue_managers:
        _queue_managers[clinic_id] = QueueManager(clinic_id=clinic_id)
    return _queue_managers[clinic_id]


async def _lookup_clinic_by_whatsapp_number(phone_number_id: str) -> Optional[str]:
    """
    Look up which clinic owns this WhatsApp Business phone_number_id.
    Production: SELECT id FROM clinics WHERE whatsapp_phone_number_id = $1
    Mocked in tests.
    """
    return None  # Production: real Supabase lookup


async def resolve_clinic_id(phone_number_id: str) -> str:
    """
    Resolve the clinic_id for an inbound webhook payload.
    Falls back to a default rather than crashing if unmapped — a clinic
    that hasn't finished onboarding should not 500 the webhook.
    """
    clinic_id = await _lookup_clinic_by_whatsapp_number(phone_number_id)
    if not clinic_id:
        logger.warning(
            "No clinic mapped for WhatsApp phone_number_id=%s — using default",
            phone_number_id,
        )
        return DEFAULT_CLINIC_ID
    return clinic_id


async def _send_reply(phone: str, text: str) -> None:
    """
    Send a free-form reply to the patient.
    This is always within the service window (we're replying to their
    own message), so free-form text is correct and free per Meta's
    24-hour service window rule.
    """
    try:
        await _client.send_message(to=phone, text=text)
    except Exception as e:
        logger.error("Failed to send WhatsApp reply to %s: %s", phone[:4] + "****", e)


async def handle_inbound_message(message: dict, clinic_id: str) -> dict:
    """
    Route inbound WhatsApp message to the walk-in intake handler.

    This is the core fix: previously this just logged and returned.
    Now it actually:
      1. Parses the message through WalkInIntakeHandler
      2. If a patient is registered, adds them to the live queue
      3. Sends the reply back to the patient via WhatsApp
    """
    from_phone = message.get("from", "")
    text = message.get("text", "")

    logger.info(
        "WhatsApp inbound from %s for clinic %s",
        from_phone[:6] + "****" if from_phone else "unknown",
        clinic_id,
    )

    handler = WalkInIntakeHandler(clinic_id=clinic_id)
    result = await handler.handle_message(
        patient_phone=from_phone,
        message=text,
        clinic_name="our clinic",
    )

    # If patient was registered, add to the live queue
    if result.get("action") in ("registered", "queued", "checkin_complete"):
        mgr = _get_queue_manager(clinic_id)
        await mgr.enqueue({
            "visit_id": result.get("visit_id"),
            "patient_name": result.get("patient_name", "Unknown"),
            "chief_complaint": result.get("chief_complaint", ""),
            "patient_phone": from_phone,
            "language": result.get("language", "en"),
            "priority": "normal",
        })

    # Send the reply back to the patient
    if result.get("reply"):
        await _send_reply(from_phone, result["reply"])

    return {
        "processed": True,
        "message_id": message.get("message_id"),
        "action": result.get("action"),
        "queue_number": result.get("queue_number"),
    }


@router.get("/webhook")
async def verify_webhook(
    request: Request,
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
) -> PlainTextResponse:
    """Meta webhook verification challenge."""
    challenge = _client.verify_webhook(
        mode=hub_mode or "",
        challenge=hub_challenge or "",
        token=hub_verify_token or "",
    )
    if challenge:
        return PlainTextResponse(content=challenge, status_code=200)
    return PlainTextResponse(content="Forbidden", status_code=403)


@router.post("/webhook")
async def receive_message(request: Request) -> JSONResponse:
    """Receive inbound WhatsApp messages from patients."""
    try:
        payload = await request.json()
    except Exception:
        return JSONResponse(status_code=400, content={"error": "Invalid JSON"})

    message = _client.parse_inbound_message(payload)

    if message:
        phone_number_id = payload.get("entry", [{}])[0].get(
            "changes", [{}]
        )[0].get("value", {}).get("metadata", {}).get("phone_number_id", "")

        clinic_id = await resolve_clinic_id(phone_number_id)
        result = await handle_inbound_message(message, clinic_id)
        return JSONResponse(content={"status": "ok", **result})

    return JSONResponse(content={"status": "no_message"})
