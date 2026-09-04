from fastapi import APIRouter,HTTPException,Request
from svix.webhooks import Webhook
from app.core.config import settings
router=APIRouter(prefix='/webhooks/clerk',tags=['webhooks'])
@router.post('')
async def clerk_webhook(request:Request):
    if not settings.clerk_webhook_secret: raise HTTPException(status_code=503,detail='clerk webhook is not configured')
    body=await request.body()
    try: Webhook(settings.clerk_webhook_secret).verify(body,dict(request.headers))
    except Exception: raise HTTPException(status_code=401,detail='invalid clerk webhook')
    return {'received':True}
