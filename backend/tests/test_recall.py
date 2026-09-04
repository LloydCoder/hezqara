"""
Recall Agent Tests — Sprint 13
TDD RED phase.

The Recall Agent proactively contacts patients for:
  - Preventive care reminders (annual checkup, flu shot)
  - Chronic disease management follow-ups (diabetes, hypertension)
  - Post-visit follow-ups
  - Appointment gap closures

Channels: SMS (Twilio), Email (Resend), Voice (Retell AI outbound),
          WhatsApp (Nigeria/SEA markets)

This agent generates the most revenue per clinic — it fills the schedule
without the clinic making a single manual call.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock


class TestRecallAgentInitialisation:

    def test_recall_agent_can_be_imported(self):
        from app.agents.recall import RecallAgent
        assert RecallAgent is not None

    def test_recall_agent_inherits_base_agent(self):
        from app.agents.recall import RecallAgent
        from app.agents.base_agent import BaseAgent
        assert issubclass(RecallAgent, BaseAgent)

    def test_recall_agent_requires_clinic_id(self):
        from app.agents.recall import RecallAgent
        with pytest.raises(TypeError):
            RecallAgent()

    def test_recall_agent_has_correct_type(self, clinic_id):
        from app.agents.recall import RecallAgent
        agent = RecallAgent(clinic_id=clinic_id)
        assert agent.agent_type == "recall"


class TestRecallAgentCampaignManagement:

    @pytest.mark.asyncio
    async def test_identify_overdue_patients(
        self, clinic_id, mock_llm_gateway, mock_graphiti, mock_ehr_client
    ):
        """Identifies patients overdue for preventive care."""
        from app.agents.recall import RecallAgent

        agent = RecallAgent(clinic_id=clinic_id)
        agent.llm = mock_llm_gateway
        agent.memory = mock_graphiti
        agent.ehr = mock_ehr_client

        mock_ehr_client.get_overdue_patients = AsyncMock(return_value=[
            {"patient_id": "PAT_001", "last_visit": "2025-06-01", "recall_type": "annual"},
            {"patient_id": "PAT_002", "last_visit": "2025-03-15", "recall_type": "annual"},
            {"patient_id": "PAT_003", "last_visit": "2026-01-20", "recall_type": "diabetes_followup"},
        ])

        patients = await agent.identify_overdue_patients(
            recall_type="annual",
            months_overdue=12,
        )

        assert len(patients) >= 1
        mock_ehr_client.get_overdue_patients.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_recall_sms_uses_local_llm(
        self, clinic_id, mock_llm_gateway, mock_graphiti
    ):
        """Recall SMS generation uses local model — never Claude."""
        from app.agents.recall import RecallAgent

        agent = RecallAgent(clinic_id=clinic_id)
        agent.llm = mock_llm_gateway
        agent.memory = mock_graphiti

        mock_llm_gateway.route.return_value = {
            "content": (
                "Hi Maria! Family Care Associates is reaching out — "
                "you're due for your annual checkup. Call us at 555-0001 to schedule."
            ),
            "model_used": "ollama/qwen2.5:14b",
            "tokens_used": 35,
            "cost_usd": 0.0,
        }

        msg = await agent.generate_recall_message(
            patient_name="Maria",
            clinic_name="Family Care Associates",
            recall_type="annual_checkup",
            channel="sms",
        )

        assert msg is not None
        assert len(msg) > 0
        call_kwargs = mock_llm_gateway.route.call_args[1]
        assert call_kwargs["task_type"] == "recall_sms_generate"

    @pytest.mark.asyncio
    async def test_generate_recall_email_uses_local_llm(
        self, clinic_id, mock_llm_gateway, mock_graphiti
    ):
        """Email recall also uses local model."""
        from app.agents.recall import RecallAgent

        agent = RecallAgent(clinic_id=clinic_id)
        agent.llm = mock_llm_gateway
        agent.memory = mock_graphiti

        mock_llm_gateway.route.return_value = {
            "content": "Dear Maria, it's time for your annual checkup...",
            "model_used": "ollama/qwen2.5:14b",
            "tokens_used": 48,
            "cost_usd": 0.0,
        }

        msg = await agent.generate_recall_message(
            patient_name="Maria",
            clinic_name="Family Care Associates",
            recall_type="annual_checkup",
            channel="email",
        )

        assert msg is not None
        call_kwargs = mock_llm_gateway.route.call_args[1]
        assert call_kwargs["task_type"] == "recall_sms_generate"


class TestRecallAgentOutreach:

    @pytest.mark.asyncio
    async def test_send_sms_recall_returns_sent(
        self, clinic_id, mock_llm_gateway, mock_graphiti
    ):
        """SMS recall sends and returns sent status."""
        from app.agents.recall import RecallAgent

        agent = RecallAgent(clinic_id=clinic_id)
        agent.llm = mock_llm_gateway
        agent.memory = mock_graphiti

        mock_sms_client = AsyncMock()
        mock_sms_client.send_sms = AsyncMock(return_value={
            "message_id": "SMS001",
            "status": "sent",
        })
        agent.sms_client = mock_sms_client

        result = await agent.send_recall_sms(
            patient_id="PAT_001",
            phone="+12125551234",
            message="Hi Maria! Time for your annual checkup.",
        )

        assert result["status"] == "sent"
        mock_sms_client.send_sms.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_recall_writes_audit_log(
        self, clinic_id, mock_llm_gateway, mock_graphiti
    ):
        """Every recall outreach writes HIPAA audit log."""
        from app.agents.recall import RecallAgent

        agent = RecallAgent(clinic_id=clinic_id)
        agent.llm = mock_llm_gateway
        agent.memory = mock_graphiti

        mock_sms_client = AsyncMock()
        mock_sms_client.send_sms = AsyncMock(return_value={
            "message_id": "SMS001", "status": "sent"
        })
        agent.sms_client = mock_sms_client

        with patch("app.agents.recall.write_audit_log") as mock_audit:
            await agent.send_recall_sms(
                patient_id="PAT_001",
                phone="+12125551234",
                message="Hi Maria! Time for your annual checkup.",
            )
            mock_audit.assert_called_once()
            kwargs = mock_audit.call_args[1]
            assert kwargs["event_type"] == "recall_sent"
            assert kwargs["clinic_id"] == clinic_id

    @pytest.mark.asyncio
    async def test_send_recall_stores_graphiti_episode(
        self, clinic_id, mock_llm_gateway, mock_graphiti
    ):
        """Recall stored in Graphiti — prevents duplicate outreach."""
        from app.agents.recall import RecallAgent

        agent = RecallAgent(clinic_id=clinic_id)
        agent.llm = mock_llm_gateway
        agent.memory = mock_graphiti

        mock_sms_client = AsyncMock()
        mock_sms_client.send_sms = AsyncMock(return_value={
            "message_id": "SMS001", "status": "sent"
        })
        agent.sms_client = mock_sms_client

        await agent.send_recall_sms(
            patient_id="PAT_001",
            phone="+12125551234",
            message="Time for your checkup.",
        )

        mock_graphiti.add_episode.assert_called_once()
        kwargs = mock_graphiti.add_episode.call_args[1]
        assert kwargs["patient_id"] == "PAT_001"

    @pytest.mark.asyncio
    async def test_sms_failure_returns_error_not_crash(
        self, clinic_id, mock_llm_gateway, mock_graphiti
    ):
        """SMS send failure returns error — never crashes campaign."""
        from app.agents.recall import RecallAgent

        agent = RecallAgent(clinic_id=clinic_id)
        agent.llm = mock_llm_gateway
        agent.memory = mock_graphiti

        mock_sms_client = AsyncMock()
        mock_sms_client.send_sms = AsyncMock(
            side_effect=Exception("Twilio rate limit")
        )
        agent.sms_client = mock_sms_client

        result = await agent.send_recall_sms(
            patient_id="PAT_001",
            phone="+12125551234",
            message="Time for your checkup.",
        )

        assert result["status"] == "failed"
        assert "error" in result


class TestRecallAgentResponseHandling:

    @pytest.mark.asyncio
    async def test_patient_response_yes_triggers_scheduling(
        self, clinic_id, mock_llm_gateway, mock_graphiti
    ):
        """When patient responds yes, route to scheduling agent."""
        from app.agents.recall import RecallAgent

        agent = RecallAgent(clinic_id=clinic_id)
        agent.llm = mock_llm_gateway
        agent.memory = mock_graphiti

        mock_llm_gateway.route.return_value = {
            "content": '{"response": "positive", "action": "schedule"}',
            "model_used": "ollama/deepseek-coder-v2",
            "tokens_used": 14,
            "cost_usd": 0.0,
        }

        result = await agent.handle_recall_response(
            patient_id="PAT_001",
            response_text="Yes I'd like to come in",
        )

        assert result["action"] == "schedule"

    @pytest.mark.asyncio
    async def test_patient_response_no_marks_declined(
        self, clinic_id, mock_llm_gateway, mock_graphiti
    ):
        """When patient declines, mark as declined in Graphiti."""
        from app.agents.recall import RecallAgent

        agent = RecallAgent(clinic_id=clinic_id)
        agent.llm = mock_llm_gateway
        agent.memory = mock_graphiti

        mock_llm_gateway.route.return_value = {
            "content": '{"response": "negative", "action": "declined"}',
            "model_used": "ollama/deepseek-coder-v2",
            "tokens_used": 12,
            "cost_usd": 0.0,
        }

        result = await agent.handle_recall_response(
            patient_id="PAT_001",
            response_text="No thanks, I'm not interested right now",
        )

        assert result["action"] == "declined"
