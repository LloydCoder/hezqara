import hashlib
import json
from redis.asyncio import Redis

class IdempotencyStore:
    def __init__(self, redis_url: str = "redis://localhost:6379/0", ttl_seconds: int = 86400):
        self.redis = Redis.from_url(redis_url, decode_responses=True)
        self.ttl_seconds = ttl_seconds
    @staticmethod
    def _key(tenant_id: str, key: str) -> str:
        digest = hashlib.sha256(f"{tenant_id}:{key}".encode()).hexdigest()
        return f"hezqara:idempotency:{digest}"
    async def get(self, tenant_id: str, key: str) -> dict | None:
        value = await self.redis.get(self._key(tenant_id, key))
        return json.loads(value) if value else None
    async def put(self, tenant_id: str, key: str, value: dict) -> bool:
        return bool(await self.redis.set(self._key(tenant_id, key), json.dumps(value, separators=(",", ":")), ex=self.ttl_seconds, nx=True))
