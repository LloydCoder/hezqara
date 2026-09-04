"""
Celery Application — async task queue for Carenova.
Broker: Redis (same instance as cache).
Beat schedule: recall campaigns, PA polling, reminders, analytics.
"""
from celery import Celery
from celery.schedules import crontab

celery_app = Celery(
    "carenova",
    broker="redis://localhost:6379/4",
    backend="redis://localhost:6379/5",
    include=[
        "app.tasks.recall_runner",
        "app.tasks.prior_auth_poller",
        "app.tasks.appointment_reminder",
        "app.tasks.analytics_rollup",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)

celery_app.conf.beat_schedule = {
    # Analytics: every day at midnight UTC
    "daily-analytics-rollup": {
        "task": "app.tasks.analytics_rollup.compute_daily_analytics",
        "schedule": crontab(hour=0, minute=0),
        "kwargs": {},
    },
    # Prior auth polling: every 4 hours
    "prior-auth-poller": {
        "task": "app.tasks.prior_auth_poller.poll_pending_prior_auths",
        "schedule": crontab(minute=0, hour="*/4"),
        "kwargs": {},
    },
    # Appointment reminders: every hour
    "appointment-reminders": {
        "task": "app.tasks.appointment_reminder.send_appointment_reminders",
        "schedule": crontab(minute=0),
        "kwargs": {"reminder_type": "24h"},
    },
}
