"""
BaseBridge — shared pattern for all Tinlance product bridges.

All 20 product bridges inherit this.
Enforces: fire-and-forget, graceful fallback, 3s timeout.
"""
import logging
from typing import Optional
import httpx

logger = logging.getLogger(__name__)


class BaseBridge:
    """Abstract base for all Tinlance ecosystem bridges."""

    product_name: str = "unknown"

    def __init__(self, url: str, api_key: str) -> None:
        self.url = url
        self.api_key = api_key

    async def _post(self, path: str, data: dict) -> dict:
        """HTTP POST to bridge endpoint. Raises on failure."""
        async with httpx.AsyncClient(timeout=3.0) as client:
            r = await client.post(
                f"{self.url}{path}",
                json=data,
                headers={
                    "X-API-Key": self.api_key,
                    "X-Source": "carenova",
                    "Content-Type": "application/json",
                },
            )
            r.raise_for_status()
            return r.json()

    def _safe_result(self, error: Exception) -> dict:
        """Standard fallback result for bridge failures."""
        logger.warning(
            "%s bridge unavailable: %s — continuing without it",
            self.product_name, str(error)
        )
        return {"sent": False, "error": str(error), "fallback": True}
