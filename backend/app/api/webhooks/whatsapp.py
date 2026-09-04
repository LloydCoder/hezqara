from fastapi import APIRouter,Request
from app.core.config import settings
from app.security.webhook import verify_whatsapp
router=APIRouter(prefix='/webhooks/whatsapp',tags=['webhooks'])
@router.post('')
async def whatsapp_webhook(request:Request):
    body=await request.body(); verify_whatsapp(body,request.headers.get('x-hub-signature-256',''),settings.whatsapp_webhook_secret); return {'received':True}
