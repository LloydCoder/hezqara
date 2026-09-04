"""Prior auth poller — checks pending PA status every 4 hours."""
import asyncio
import logging
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


async def _poll(clinic_id: str, tracking_numbers: list) -> dict:
    from app.agents.prior_auth import PriorAuthAgent
    agent = PriorAuthAgent(clinic_id=clinic_id or "system")
    checked = 0
    for tn in tracking_numbers:
        try:
            await agent.check_pa_status(call_id=f"poller_{tn}", tracking_number=tn)
            checked += 1
        except Exception as e:
            logger.error("PA poll failed for %s: %s", tn, str(e))
    return {"status": "completed", "clinic_id": clinic_id, "checked": checked}


@celery_app.task(name="app.tasks.prior_auth_poller.poll_pending_prior_auths", bind=True)
def poll_pending_prior_auths(self, clinic_id: str = "", tracking_numbers: list = None) -> dict:
    """Poll payer portals for pending prior auth decisions."""
    return asyncio.run(_poll(clinic_id, tracking_numbers or []))
