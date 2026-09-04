import hashlib,hmac
from fastapi import HTTPException

def verify_hmac(raw_body:bytes,signature:str,secret:str,algorithm='sha256',prefix=''):
    if not secret: raise HTTPException(status_code=503,detail='webhook verification is not configured')
    supplied=signature.removeprefix(prefix)
    expected=hmac.new(secret.encode(),raw_body,getattr(hashlib,algorithm)).hexdigest()
    if not hmac.compare_digest(expected,supplied): raise HTTPException(status_code=401,detail='invalid webhook signature')

def verify_whatsapp(raw_body:bytes,signature:str,secret:str): verify_hmac(raw_body,signature,secret,prefix='sha256=')
