"""Celery application for asynchronous HEZQARA workflows."""
from celery import Celery
from celery.schedules import crontab

from app.config import settings

celery_app = Celery(
    "hezqara",
    broker=settings.redis_url,
    backend=settings.redis_url,
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
    task_default_queue="hezqara",
)

celery_app.conf.beat_schedule = {
    "daily-analytics-rollup": {
        "task": "app.tasks.analytics_rollup.compute_daily_analytics",
        "schedule": crontab(hour=0, minute=0),
    },
    "prior-auth-poller": {
        "task": "app.tasks.prior_auth_poller.poll_pending_prior_auths",
        "schedule": crontab(minute=0, hour="*/4"),
    },
    "appointment-reminders": {
        "task": "app.tasks.appointment_reminder.send_appointment_reminders",
        "schedule": crontab(minute=0),
        "kwargs": {"reminder_type": "24h"},
    },
}
