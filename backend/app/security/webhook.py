import hashlib,hmac
from redis.asyncio import Redis
from fastapi import HTTPException
from app.core.config import settings

def verify_hmac(raw_body:bytes,signature:str,secret:str,algorithm='sha256',prefix=''):
    if not secret: raise HTTPException(status_code=503,detail='webhook verification is not configured')
    supplied=signature.removeprefix(prefix); expected=hmac.new(secret.encode(),raw_body,getattr(hashlib,algorithm)).hexdigest()
    if not hmac.compare_digest(expected,supplied): raise HTTPException(status_code=401,detail='invalid webhook signature')

def verify_whatsapp(raw_body:bytes,signature:str,secret:str): verify_hmac(raw_body,signature,secret,prefix='sha256=')

class WebhookReplayStore:
    def __init__(self): self.redis=Redis.from_url(settings.redis_url,decode_responses=True)
    async def claim(self,provider:str,event_id:str,ttl_seconds:int=172800)->bool:
        if not event_id or len(event_id)>300: raise HTTPException(status_code=400,detail='valid webhook event id required')
        key=hashlib.sha256(f"{provider}:{event_id}".encode()).hexdigest()
        return bool(await self.redis.set(f"hezqara:webhook:{key}","1",nx=True,ex=ttl_seconds))
    async def close(self): await self.redis.aclose()
