import stripe
from fastapi import APIRouter,HTTPException,Request
from app.core.config import settings
from app.security.webhook import WebhookReplayStore
router=APIRouter(prefix='/webhooks/stripe',tags=['webhooks']); replay=WebhookReplayStore()
@router.post('')
async def stripe_webhook(request:Request):
    if not settings.stripe_webhook_secret: raise HTTPException(status_code=503,detail='stripe webhook is not configured')
    body=await request.body(); sig=request.headers.get('stripe-signature','')
    try: event=stripe.Webhook.construct_event(body,sig,settings.stripe_webhook_secret)
    except (ValueError,stripe.error.SignatureVerificationError) as exc: raise HTTPException(status_code=400,detail='invalid stripe webhook') from exc
    event_id=event.get('id')
    if not event_id: raise HTTPException(status_code=400,detail='stripe event id required')
    if not await replay.claim('stripe',event_id): return {'received':True,'event_id':event_id,'duplicate':True}
    return {'received':True,'event_id':event_id,'type':event.get('type')}
