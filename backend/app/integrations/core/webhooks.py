import hashlib
import hmac
import time

class WebhookSecurityError(ValueError): pass

def verify_hmac_signature(payload: bytes, signature: str, secret: str, timestamp: int, *, tolerance_seconds: int=300, now: int|None=None) -> None:
    if not secret or not signature: raise WebhookSecurityError('signature is required')
    current=int(time.time()) if now is None else now
    if abs(current-timestamp)>tolerance_seconds: raise WebhookSecurityError('webhook timestamp outside replay window')
    expected=hmac.new(secret.encode(),f'{timestamp}.'.encode()+payload,hashlib.sha256).hexdigest()
    supplied=signature.removeprefix('sha256=')
    if not hmac.compare_digest(expected,supplied): raise WebhookSecurityError('invalid webhook signature')

class ReplayGuard:
    def __init__(self)->None: self._seen:set[str]=set()
    def accept(self,event_id:str)->bool:
        if not event_id or event_id in self._seen: return False
        self._seen.add(event_id); return True
