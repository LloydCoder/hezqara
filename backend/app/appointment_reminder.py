"""Appointment reminder — sends 24h and 2h reminders via email/SMS."""
import asyncio
import logging
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


async def _send_reminders(clinic_id: str, appointments: list, reminder_type: str) -> dict:
    from app.agents.email_agent import EmailAgent
    agent = EmailAgent(clinic_id=clinic_id or "system")
    sent = 0
    for appt in appointments:
        try:
            await agent.send_email(
                to=appt.get("patient_email", ""),
                subject=f"Appointment Reminder — {appt.get('datetime', '')}",
                body=(
                    f"Hi {appt.get('patient_name', 'there')}! "
                    f"Reminder: appointment with {appt.get('provider', 'your provider')} "
                    f"on {appt.get('datetime', '')}."
                ),
                patient_id=appt.get("patient_id", ""),
            )
            sent += 1
        except Exception as e:
            logger.error("Reminder failed for %s: %s", appt.get("appointment_id"), str(e))
    return {"status": "completed", "clinic_id": clinic_id, "reminder_type": reminder_type, "reminders_sent": sent}


@celery_app.task(name="app.tasks.appointment_reminder.send_appointment_reminders", bind=True)
def send_appointment_reminders(self, clinic_id: str = "", appointments: list = None, reminder_type: str = "24h") -> dict:
    """Send appointment reminders to patients."""
    return asyncio.run(_send_reminders(clinic_id, appointments or [], reminder_type))
