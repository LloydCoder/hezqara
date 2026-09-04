from fastapi import APIRouter,Request
from app.core.config import settings
from app.security.webhook import verify_hmac
router=APIRouter(prefix="/webhooks/clerk",tags=["webhooks"])
@router.post("")
async def clerk_webhook(request:Request):
    body=await request.body(); verify_hmac(body,request.headers.get("x-hezqara-signature", ""),settings.clerk_webhook_secret); return {"received":True}
