from fastapi import APIRouter,HTTPException,Request
from app.core.config import settings
from app.security.webhook import WebhookReplayStore,verify_hmac
router=APIRouter(prefix='/webhooks/retell',tags=['webhooks']); replay=WebhookReplayStore()
@router.post('')
async def retell_webhook(request:Request):
    body=await request.body(); verify_hmac(body,request.headers.get('x-retell-signature',''),settings.retell_webhook_secret)
    try: payload=await request.json()
    except Exception as exc: raise HTTPException(status_code=400,detail='invalid JSON webhook') from exc
    event_id=str(payload.get('event_id') or payload.get('call_id') or '')
    if not event_id: raise HTTPException(status_code=400,detail='retell event id required')
    if not await replay.claim('retell',event_id): return {'received':True,'event_id':event_id,'duplicate':True}
    return {'received':True,'event_id':event_id}
