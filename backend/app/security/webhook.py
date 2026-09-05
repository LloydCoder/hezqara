import hashlib
import hmac

from fastapi import HTTPException
from redis.asyncio import Redis

from app.core.config import settings


def verify_hmac(
    raw_body: bytes,
    signature: str,
    secret: str,
    algorithm: str = "sha256",
    prefix: str = "",
) -> None:
    if not secret:
        raise HTTPException(status_code=503, detail="webhook verification is not configured")
    supplied = signature.removeprefix(prefix)
    expected = hmac.new(secret.encode(), raw_body, getattr(hashlib, algorithm)).hexdigest()
    if not hmac.compare_digest(expected, supplied):
        raise HTTPException(status_code=401, detail="invalid webhook signature")


def verify_whatsapp(raw_body: bytes, signature: str, secret: str) -> None:
    verify_hmac(raw_body, signature, secret, prefix="sha256=")


class WebhookReplayStore:
    """Redis-backed replay protection with explicit unavailable behavior.

    Importing the application must not require Redis to be configured, but
    production webhook processing must fail closed when replay protection is
    unavailable rather than silently falling back to process-local state.
    """

    def __init__(self) -> None:
        self.redis: Redis | None = (
            Redis.from_url(settings.redis_url, decode_responses=True)
            if settings.redis_url
            else None
        )

    async def claim(self, provider: str, event_id: str, ttl_seconds: int = 172800) -> bool:
        if not event_id or len(event_id) > 300:
            raise HTTPException(status_code=400, detail="valid webhook event id required")
        if self.redis is None:
            raise HTTPException(status_code=503, detail="webhook replay protection is not configured")
        key = hashlib.sha256(f"{provider}:{event_id}".encode()).hexdigest()
        return bool(await self.redis.set(f"hezqara:webhook:{key}", "1", nx=True, ex=ttl_seconds))

    async def close(self) -> None:
        if self.redis is not None:
            await self.redis.aclose()
