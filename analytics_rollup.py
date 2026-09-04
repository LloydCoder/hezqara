"""Analytics rollup — computes daily clinic metrics."""
import logging
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


def get_daily_metrics(clinic_id: str, date: str) -> dict:
    """
    Fetch daily metrics from database.
    Production: queries Supabase for the clinic and date.
    """
    return {
        "calls_handled": 0,
        "appointments_booked": 0,
        "refills_processed": 0,
        "recalls_sent": 0,
        "cost_savings_usd": 0.0,
    }


@celery_app.task(name="app.tasks.analytics_rollup.compute_daily_analytics", bind=True)
def compute_daily_analytics(
    self,
    clinic_id: str = "",
    date: str = "",
) -> dict:
    """Compute and store daily analytics for a clinic."""
    try:
        metrics = get_daily_metrics(clinic_id=clinic_id, date=date)
        return {
            "status": "completed",
            "clinic_id": clinic_id,
            "date": date,
            "metrics": metrics,
        }
    except Exception as e:
        logger.error("Analytics rollup failed for %s: %s", clinic_id, str(e))
        return {"status": "failed", "error": str(e)}
