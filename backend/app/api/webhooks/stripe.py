import stripe
from fastapi import APIRouter, HTTPException, Request

from app.core.config import settings
from app.infrastructure.database import system_session_context
from app.platform.commercial import apply_provider_event
from app.security.webhook import WebhookReplayStore

router = APIRouter(prefix="/webhooks/stripe", tags=["webhooks"])
replay = WebhookReplayStore()


@router.post("")
async def stripe_webhook(request: Request):
    if not settings.stripe_webhook_secret:
        raise HTTPException(status_code=503, detail="stripe webhook is not configured")

    body = await request.body()
    signature = request.headers.get("stripe-signature", "")
    try:
        event = stripe.Webhook.construct_event(
            body,
            signature,
            settings.stripe_webhook_secret,
        )
    except (ValueError, stripe.error.SignatureVerificationError) as exc:
        raise HTTPException(status_code=400, detail="invalid stripe webhook") from exc

    event_id = event.get("id")
    if not event_id:
        raise HTTPException(status_code=400, detail="stripe event id required")

    # Redis is a fast duplicate filter; PostgreSQL subscription_events is the
    # durable idempotency authority so correctness does not depend on Redis.
    if not await replay.claim("stripe", event_id):
        return {"received": True, "event_id": event_id, "duplicate": True}

    try:
        async with system_session_context() as session:
            result = await apply_provider_event(session, event)
    except Exception as exc:
        # Return a non-2xx response so Stripe retries delivery. The durable
        # event record is only marked processed after the state transition
        # succeeds.
        raise HTTPException(status_code=500, detail="stripe event processing failed") from exc

    return {
        "received": True,
        "event_id": event_id,
        "type": event.get("type"),
        **result,
    }
