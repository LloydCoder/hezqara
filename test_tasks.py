"""
Celery Async Tasks Tests — Sprint 16
TDD RED phase.

Long-running operations run as Celery tasks:
  - recall_runner: fires recall campaigns on schedule
  - prior_auth_poller: polls payer portals every 4 hours
  - appointment_reminder: sends 24h and 2h reminders
  - analytics_rollup: computes daily clinic metrics
  - claims_follower: follows up on aging claims

These tasks are the backbone of the platform's automation value.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestCeleryAppConfiguration:

    def test_celery_app_can_be_imported(self):
        from app.tasks.celery_app import celery_app
        assert celery_app is not None

    def test_celery_app_has_correct_name(self):
        from app.tasks.celery_app import celery_app
        assert celery_app.main == "carenova"

    def test_celery_app_uses_redis_broker(self):
        from app.tasks.celery_app import celery_app
        assert "redis" in celery_app.conf.broker_url


class TestRecallRunnerTask:

    def test_recall_runner_task_exists(self):
        from app.tasks.recall_runner import run_recall_campaign
        assert run_recall_campaign is not None

    def test_recall_runner_is_celery_task(self):
        from app.tasks.recall_runner import run_recall_campaign
        assert hasattr(run_recall_campaign, "delay")

    @patch("app.agents.recall.RecallAgent")
    def test_recall_runner_creates_recall_agent(self, MockAgent):
        """Task creates a RecallAgent for the correct clinic."""
        from app.tasks.recall_runner import run_recall_campaign

        mock_agent = MagicMock()
        mock_agent.identify_overdue_patients = AsyncMock(return_value=[])
        MockAgent.return_value = mock_agent

        run_recall_campaign(
            clinic_id="clinic_test_001",
            recall_type="annual",
            months_overdue=12,
        )

        MockAgent.assert_called_once_with(clinic_id="clinic_test_001")

    @patch("app.agents.recall.RecallAgent")
    def test_recall_runner_handles_empty_patient_list(self, MockAgent):
        """Empty patient list does not crash the task."""
        from app.tasks.recall_runner import run_recall_campaign

        mock_agent = MagicMock()
        mock_agent.identify_overdue_patients = AsyncMock(return_value=[])
        MockAgent.return_value = mock_agent

        result = run_recall_campaign(
            clinic_id="clinic_test_001",
            recall_type="annual",
            months_overdue=12,
        )

        assert result["status"] == "completed"
        assert result["patients_contacted"] == 0


class TestPriorAuthPollerTask:

    def test_prior_auth_poller_exists(self):
        from app.tasks.prior_auth_poller import poll_pending_prior_auths
        assert poll_pending_prior_auths is not None

    def test_prior_auth_poller_is_celery_task(self):
        from app.tasks.prior_auth_poller import poll_pending_prior_auths
        assert hasattr(poll_pending_prior_auths, "delay")

    @patch("app.agents.prior_auth.PriorAuthAgent")
    def test_poller_checks_pending_auths(self, MockAgent):
        """Task polls all pending prior auths for a clinic."""
        from app.tasks.prior_auth_poller import poll_pending_prior_auths

        mock_agent = MagicMock()
        mock_agent.check_pa_status = AsyncMock(return_value={"status": "pending"})
        MockAgent.return_value = mock_agent

        result = poll_pending_prior_auths(
            clinic_id="clinic_test_001",
            tracking_numbers=["PA-001", "PA-002"],
        )

        assert result["status"] == "completed"
        assert result["checked"] == 2


class TestAppointmentReminderTask:

    def test_appointment_reminder_task_exists(self):
        from app.tasks.appointment_reminder import send_appointment_reminders
        assert send_appointment_reminders is not None

    def test_appointment_reminder_is_celery_task(self):
        from app.tasks.appointment_reminder import send_appointment_reminders
        assert hasattr(send_appointment_reminders, "delay")

    @patch("app.agents.email_agent.EmailAgent")
    def test_reminder_sends_email_to_patient(self, MockAgent):
        """Task sends reminder email for upcoming appointment."""
        from app.tasks.appointment_reminder import send_appointment_reminders

        mock_agent = MagicMock()
        mock_agent.send_email = AsyncMock(return_value={"status": "sent"})
        MockAgent.return_value = mock_agent

        appointments = [{
            "appointment_id": "APT001",
            "patient_email": "maria@example.com",
            "patient_name": "Maria",
            "provider": "Dr. Chen",
            "datetime": "2026-07-01T09:00:00",
        }]

        result = send_appointment_reminders(
            clinic_id="clinic_test_001",
            appointments=appointments,
            reminder_type="24h",
        )

        assert result["status"] == "completed"
        assert result["reminders_sent"] == 1


class TestAnalyticsRollupTask:

    def test_analytics_rollup_task_exists(self):
        from app.tasks.analytics_rollup import compute_daily_analytics
        assert compute_daily_analytics is not None

    def test_analytics_rollup_is_celery_task(self):
        from app.tasks.analytics_rollup import compute_daily_analytics
        assert hasattr(compute_daily_analytics, "delay")

    @patch("app.tasks.analytics_rollup.get_daily_metrics")
    def test_rollup_returns_metrics_dict(self, mock_metrics):
        """Rollup computes and returns daily metrics."""
        from app.tasks.analytics_rollup import compute_daily_analytics

        mock_metrics.return_value = {
            "calls_handled": 47,
            "appointments_booked": 23,
            "refills_processed": 8,
            "recalls_sent": 15,
            "cost_savings_usd": 387.50,
        }

        result = compute_daily_analytics(
            clinic_id="clinic_test_001",
            date="2026-07-01",
        )

        assert result["status"] == "completed"
        assert "metrics" in result
        assert result["metrics"]["calls_handled"] == 47


class TestCeleryBeatSchedule:

    def test_beat_schedule_configured(self):
        """Celery Beat periodic tasks are configured."""
        from app.tasks.celery_app import celery_app

        beat = celery_app.conf.beat_schedule
        assert beat is not None
        assert len(beat) > 0

    def test_analytics_rollup_scheduled_daily(self):
        """Daily analytics rollup is in beat schedule."""
        from app.tasks.celery_app import celery_app

        beat = celery_app.conf.beat_schedule
        task_names = [v.get("task", "") for v in beat.values()]
        assert any("analytics" in t for t in task_names)

    def test_prior_auth_poller_scheduled(self):
        """Prior auth polling is in beat schedule."""
        from app.tasks.celery_app import celery_app

        beat = celery_app.conf.beat_schedule
        task_names = [v.get("task", "") for v in beat.values()]
        assert any("prior_auth" in t for t in task_names)
