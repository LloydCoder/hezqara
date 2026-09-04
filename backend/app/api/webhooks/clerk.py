from fastapi import APIRouter,HTTPException,Request
from svix.webhooks import Webhook
from app.core.config import settings
from app.security.webhook import WebhookReplayStore
router=APIRouter(prefix='/webhooks/clerk',tags=['webhooks']); replay=WebhookReplayStore()
@router.post('')
async def clerk_webhook(request:Request):
    if not settings.clerk_webhook_secret: raise HTTPException(status_code=503,detail='clerk webhook is not configured')
    body=await request.body()
    try: Webhook(settings.clerk_webhook_secret).verify(body,dict(request.headers))
    except Exception as exc: raise HTTPException(status_code=401,detail='invalid clerk webhook') from exc
    event_id=request.headers.get('svix-id')
    if not event_id: raise HTTPException(status_code=400,detail='clerk event id required')
    if not await replay.claim('clerk',event_id): return {'received':True,'event_id':event_id,'duplicate':True}
    return {'received':True,'event_id':event_id}
