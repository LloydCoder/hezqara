"""
AI Shield Bridge — prompt injection and PHI protection.
EC2 Stockholm: 13.50.16.19:8002
Exception: AI Shield connects directly (not via FusionOps) — surveillance infrastructure.
Fail-safe: timeout defaults to safe=True — never block patient care.
"""
import logging
import httpx

logger = logging.getLogger(__name__)


class AIShieldBridge:
    """Scans agent prompts for injection attacks and PHI leakage."""

    def __init__(self, url: str, api_key: str) -> None:
        self.url = url
        self.api_key = api_key

    async def scan_prompt(
        self,
        prompt: str,
        clinic_id: str,
        agent_type: str,
    ) -> dict:
        """
        Scan prompt for injection attempts.
        Timeout/failure defaults to safe=True — patient care is never blocked.
        """
        try:
            result = await self._post(
                "/scan",
                {
                    "prompt": prompt,
                    "clinic_id": clinic_id,
                    "agent_type": agent_type,
                    "source": "carenova",
                },
            )
            return {
                "safe": result.get("safe", True),
                "threat_score": result.get("threat_score", 0.0),
                "threats_detected": result.get("threats_detected", []),
            }
        except (httpx.TimeoutException, httpx.ConnectError) as e:
            logger.warning("AI Shield unavailable: %s — defaulting to safe", str(e))
            return {"safe": True, "threat_score": 0.0, "threats_detected": [], "fallback": True}
        except Exception as e:
            logger.error("AI Shield scan error: %s", str(e))
            return {"safe": True, "threat_score": 0.0, "threats_detected": [], "fallback": True}

    async def _post(self, path: str, data: dict) -> dict:
        async with httpx.AsyncClient(timeout=2.0) as client:
            r = await client.post(
                f"{self.url}{path}",
                json=data,
                headers={"X-API-Key": self.api_key},
            )
            r.raise_for_status()
            return r.json()
