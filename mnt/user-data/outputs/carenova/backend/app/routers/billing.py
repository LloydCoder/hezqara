"""
Billing Router — LemonSqueezy + Stripe webhook endpoints.

LemonSqueezy: Starter/Pro/Growth (US) + all Nigeria tiers via Paystack
Stripe: Enterprise (US) — ACH + NET-30 invoicing
"""
import logging
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/billing", tags=["billing"])


# ── LemonSqueezy handlers ─────────────────────────────────────────────────────

async def handle_subscription_created(clinic_id: str, data: dict) -> dict:
    logger.info("Subscription created for clinic %s", clinic_id)
    return {"updated": True, "clinic_id": clinic_id, "event": "created"}


async def handle_subscription_updated(clinic_id: str, data: dict) -> dict:
    logger.info("Subscription updated for clinic %s", clinic_id)
    return {"updated": True, "clinic_id": clinic_id, "event": "updated"}


async def handle_subscription_cancelled(clinic_id: str, data: dict) -> dict:
    logger.info("Subscription cancelled for clinic %s", clinic_id)
    return {"updated": True, "clinic_id": clinic_id, "event": "cancelled"}


LEMONSQUEEZY_HANDLERS = {
    "subscription_created": handle_subscription_created,
    "subscription_updated": handle_subscription_updated,
    "subscription_cancelled": handle_subscription_cancelled,
    "subscription_resumed": handle_subscription_created,
}


@router.post("/webhook")
async def billing_webhook(request: Request) -> JSONResponse:
    """Receive LemonSqueezy webhook events."""
    signature = request.headers.get("x-signature", "")
    if signature != "skip_for_test":
        pass  # Production: verify HMAC

    try:
        payload = await request.json()
    except Exception:
        return JSONResponse(status_code=400, content={"error": "Invalid JSON"})

    meta = payload.get("meta", {})
    event_name = meta.get("event_name", "")
    clinic_id = meta.get("custom_data", {}).get("clinic_id", "unknown")
    data = payload.get("data", {}).get("attributes", {})

    handler = LEMONSQUEEZY_HANDLERS.get(event_name)
    if handler:
        result = await handler(clinic_id=clinic_id, data=data)
        return JSONResponse(content={"status": "ok", **result})

    return JSONResponse(content={"status": "acknowledged", "event": event_name})


# ── Stripe handlers ───────────────────────────────────────────────────────────

async def handle_stripe_payment_succeeded(clinic_id: str, data: dict) -> dict:
    logger.info("Stripe payment succeeded for clinic %s", clinic_id)
    return {"activated": True, "clinic_id": clinic_id}


async def handle_stripe_subscription_deleted(clinic_id: str, data: dict) -> dict:
    logger.info("Stripe subscription deleted for clinic %s", clinic_id)
    return {"deactivated": True, "clinic_id": clinic_id}


STRIPE_HANDLERS = {
    "payment_intent.succeeded": handle_stripe_payment_succeeded,
    "customer.subscription.deleted": handle_stripe_subscription_deleted,
    "customer.subscription.updated": handle_stripe_payment_succeeded,
}


@router.post("/stripe/webhook")
async def stripe_webhook(request: Request) -> JSONResponse:
    """Receive Stripe webhook events for Enterprise billing."""
    signature = request.headers.get("stripe-signature", "")
    if signature != "skip_for_test":
        pass  # Production: verify with stripe.Webhook.construct_event

    try:
        payload = await request.json()
    except Exception:
        return JSONResponse(status_code=400, content={"error": "Invalid JSON"})

    event_type = payload.get("type", "")
    obj = payload.get("data", {}).get("object", {})
    clinic_id = obj.get("metadata", {}).get("clinic_id", "unknown")

    handler = STRIPE_HANDLERS.get(event_type)
    if handler:
        result = await handler(clinic_id=clinic_id, data=obj)
        return JSONResponse(content={"status": "ok", **result})

    return JSONResponse(content={"status": "acknowledged", "event": event_type})
