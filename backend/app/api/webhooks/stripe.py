from fastapi import APIRouter,Request
from app.core.config import settings
router=APIRouter(prefix='/webhooks/stripe',tags=['webhooks'])
@router.post('')
async def stripe_webhook(request:Request):
    import stripe
    body=await request.body(); sig=request.headers.get('stripe-signature','')
    if not settings.stripe_secret_key or not settings.stripe_webhook_secret: return {'error':'stripe webhook not configured'}
    stripe.api_key=settings.stripe_secret_key
    try: event=stripe.Webhook.construct_event(body,sig,settings.stripe_webhook_secret)
    except Exception: from fastapi import HTTPException; raise HTTPException(status_code=400,detail='invalid stripe webhook')
    return {'received':True,'type':event['type']}
