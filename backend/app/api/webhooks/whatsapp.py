from fastapi import APIRouter,HTTPException,Request
from app.core.config import settings
from app.security.webhook import verify_whatsapp,WebhookReplayStore
router=APIRouter(prefix='/webhooks/whatsapp',tags=['webhooks']); replay=WebhookReplayStore()
@router.post('')
async def whatsapp_webhook(request:Request):
    body=await request.body(); verify_whatsapp(body,request.headers.get('x-hub-signature-256',''),settings.whatsapp_webhook_secret)
    try: payload=await request.json()
    except Exception as exc: raise HTTPException(status_code=400,detail='invalid JSON webhook') from exc
    messages=((payload.get('entry') or [{}])[0].get('changes') or [{}])[0].get('value',{}).get('messages') or []
    event_id=str(messages[0].get('id') if messages else request.headers.get('x-request-id',''))
    if not event_id: raise HTTPException(status_code=400,detail='whatsapp event id required')
    if not await replay.claim('whatsapp',event_id): return {'received':True,'event_id':event_id,'duplicate':True}
    return {'received':True,'event_id':event_id}
