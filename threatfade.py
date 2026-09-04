"""
ThreatFade Bridge — fraud Z-score on patient transactions.
EC2 Stockholm: 13.50.16.19:8000
Production-validated: Merlin QUIC C2 malware, Z-score 14.76.
Threshold: Z-score > 14.76 = critical threat (MITRE T1027).
Graceful fallback: returns Z-score 0.0 if ThreatFade is down.
"""
import logging
import httpx

logger = logging.getLogger(__name__)

CRITICAL_ZSCORE_THRESHOLD = 14.76


class ThreatFadeBridge:
    """Scores patient transactions for fraud and anomaly detection."""

    def __init__(self, url: str, api_key: str) -> None:
        self.url = url
        self.api_key = api_key

    async def score_transaction(
        self,
        transaction_type: str,
        clinic_id: str,
        patient_id: str,
        payload: dict,
    ) -> dict:
        """
        Score a transaction for fraud signals.
        Returns Z-score and threat level.
        Failure returns safe default — never blocks care.
        """
        try:
            result = await self._post(
                "/score",
                {
                    "transaction_type": transaction_type,
                    "clinic_id": clinic_id,
                    "patient_id": patient_id,
                    "source": "carenova",
                    "payload": payload,
                },
            )
            return {
                "z_score": result.get("z_score", 0.0),
                "threat_level": result.get("threat_level", "low"),
                "mitre_tags": result.get("mitre_tags", []),
            }
        except Exception as e:
            logger.warning("ThreatFade unavailable: %s — returning safe default", str(e))
            return {
                "z_score": 0.0,
                "threat_level": "low",
                "mitre_tags": [],
                "fallback": True,
            }

    async def _post(self, path: str, data: dict) -> dict:
        async with httpx.AsyncClient(timeout=3.0) as client:
            r = await client.post(
                f"{self.url}{path}",
                json=data,
                headers={"X-API-Key": self.api_key},
            )
            r.raise_for_status()
            return r.json()
