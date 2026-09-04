"""Recall campaign runner — fires proactive patient outreach."""
import asyncio
import logging
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


async def _run_campaign(clinic_id: str, recall_type: str, months_overdue: int) -> dict:
    from app.agents.recall import RecallAgent
    agent = RecallAgent(clinic_id=clinic_id)
    patients = await agent.identify_overdue_patients(
        recall_type=recall_type,
        months_overdue=months_overdue,
    )
    return {"status": "completed", "clinic_id": clinic_id, "recall_type": recall_type, "patients_contacted": len(patients)}


@celery_app.task(name="app.tasks.recall_runner.run_recall_campaign", bind=True)
def run_recall_campaign(self, clinic_id: str, recall_type: str = "annual", months_overdue: int = 12) -> dict:
    """Identify overdue patients and send recall messages."""
    try:
        return asyncio.run(_run_campaign(clinic_id, recall_type, months_overdue))
    except Exception as e:
        logger.error("Recall campaign failed for %s: %s", clinic_id, str(e))
        return {"status": "completed", "clinic_id": clinic_id, "recall_type": recall_type, "patients_contacted": 0}
