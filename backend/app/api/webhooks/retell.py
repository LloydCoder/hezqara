from fastapi import APIRouter,Request
from app.core.config import settings
from app.security.webhook import verify_hmac
router=APIRouter(prefix='/webhooks/retell',tags=['webhooks'])
@router.post('')
async def retell_webhook(request:Request):
    body=await request.body(); verify_hmac(body,request.headers.get('x-retell-signature',''),settings.retell_webhook_secret); return {'received':True}
