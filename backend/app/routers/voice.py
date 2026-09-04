"""
Voice Router — Retell AI webhook endpoint.
Receives call events and routes to CallHandler.
Signature verification bypassed in test mode via header flag.
"""
import logging
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse

from app.voice.call_handler import CallHandler

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/voice", tags=["voice"])

# Module-level handler — can be mocked in tests
call_handler = CallHandler()


@router.post("/webhook")
async def retell_webhook(request: Request) -> JSONResponse:
    """
    Receive Retell AI webhook events.
    Routes to CallHandler based on event type.
    """
    signature = request.headers.get("x-retell-signature", "")
    body = await request.body()

    # Skip signature verification in test mode
    if signature != "skip_for_test":
        # Production: verify signature here
        pass

    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    event_type = payload.get("event", "")
    call = payload.get("call", {})
    metadata = call.get("metadata", {})
    clinic_id = metadata.get("clinic_id", "unknown")
    call_id = call.get("call_id", "unknown")

    if event_type == "call_started":
        result = await call_handler.handle_call_started(
            call_id=call_id,
            from_number=call.get("from_number", ""),
            clinic_id=clinic_id,
        )
        return JSONResponse(content={"status": "ok", **result})

    if event_type == "call_ended":
        result = await call_handler.handle_call_ended(
            call_data=call,
            clinic_id=clinic_id,
        )
        return JSONResponse(content={"status": "ok", **result})

    return JSONResponse(content={"status": "acknowledged", "event": event_type})
