"""
ResilientAI Bridge — uptime monitoring and health reporting.
EC2 Stockholm: 13.50.16.19:8003
Carenova pings ResilientAI on startup and every minute.
"""
import logging
import httpx

logger = logging.getLogger(__name__)


class ResilientAIBridge:
    """Reports Carenova health and metrics to ResilientAI."""

    def __init__(self, url: str, api_key: str) -> None:
        self.url = url
        self.api_key = api_key

    async def send_health_ping(
        self,
        service: str,
        port: int,
        status: str = "healthy",
    ) -> dict:
        """Send health ping to ResilientAI."""
        try:
            result = await self._post(
                "/ping",
                {"service": service, "port": port, "status": status},
            )
            return {"sent": True, "result": result}
        except Exception as e:
            logger.warning("ResilientAI ping failed: %s", str(e))
            return {"sent": False, "error": str(e)}

    async def report_metric(
        self,
        metric_name: str,
        value: float,
        clinic_id: str,
    ) -> dict:
        """Report operational metric to ResilientAI."""
        try:
            result = await self._post(
                "/metrics",
                {
                    "source": "carenova",
                    "metric": metric_name,
                    "value": value,
                    "clinic_id": clinic_id,
                },
            )
            return {"sent": True, "result": result}
        except Exception as e:
            logger.warning("ResilientAI metric failed: %s", str(e))
            return {"sent": False, "error": str(e)}

    async def _post(self, path: str, data: dict) -> dict:
        async with httpx.AsyncClient(timeout=3.0) as client:
            r = await client.post(
                f"{self.url}{path}",
                json=data,
                headers={"X-API-Key": self.api_key},
            )
            r.raise_for_status()
            return r.json()
