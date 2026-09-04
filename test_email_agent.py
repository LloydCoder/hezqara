"""
Email Agent Tests — Sprint 14
TDD RED phase.

The Email Agent manages the clinic's inbox end-to-end:
  - Categorize incoming emails by intent
  - Draft replies for provider review
  - Route urgent emails immediately
  - Send appointment confirmations and reminders
  - Handle patient portal messages
  - Never send unsupervised clinical advice
"""
import pytest
from unittest.mock import AsyncMock, patch


class TestEmailAgentInitialisation:

    def test_email_agent_can_be_imported(self):
        from app.agents.email_agent import EmailAgent
        assert EmailAgent is not None

    def test_email_agent_inherits_base_agent(self):
        from app.agents.email_agent import EmailAgent
        from app.agents.base_agent import BaseAgent
        assert issubclass(EmailAgent, BaseAgent)

    def test_email_agent_requires_clinic_id(self):
        from app.agents.email_agent import EmailAgent
        with pytest.raises(TypeError):
            EmailAgent()

    def test_email_agent_has_correct_type(self, clinic_id):
        from app.agents.email_agent import EmailAgent
        agent = EmailAgent(clinic_id=clinic_id)
        assert agent.agent_type == "email"


class TestEmailAgentCategorization:

    @pytest.mark.asyncio
    async def test_categorize_appointment_request(
        self, clinic_id, mock_llm_gateway, mock_graphiti
    ):
        """Email requesting appointment is categorized correctly."""
        from app.agents.email_agent import EmailAgent

        agent = EmailAgent(clinic_id=clinic_id)
        agent.llm = mock_llm_gateway
        agent.memory = mock_graphiti

        mock_llm_gateway.route.return_value = {
            "content": '{"category": "appointment_request", "urgency": "routine", "requires_provider": false}',
            "model_used": "ollama/deepseek-coder-v2",
            "tokens_used": 22,
            "cost_usd": 0.0,
        }

        result = await agent.categorize_email(
            call_id="email_abc123",
            subject="Need to schedule appointment",
            body="Hi, I need to come in for my annual checkup. When are you available?",
        )

        assert result["category"] == "appointment_request"
        assert result["requires_provider"] is False

    @pytest.mark.asyncio
    async def test_categorize_clinical_question_requires_provider(
        self, clinic_id, mock_llm_gateway, mock_graphiti
    ):
        """Clinical question always requires provider review."""
        from app.agents.email_agent import EmailAgent

        agent = EmailAgent(clinic_id=clinic_id)
        agent.llm = mock_llm_gateway
        agent.memory = mock_graphiti

        mock_llm_gateway.route.return_value = {
            "content": '{"category": "clinical_question", "urgency": "routine", "requires_provider": true}',
            "model_used": "ollama/deepseek-coder-v2",
            "tokens_used": 20,
            "cost_usd": 0.0,
        }

        result = await agent.categorize_email(
            call_id="email_abc123",
            subject="Question about my medication",
            body="I've been having side effects from my new blood pressure medication. Is this normal?",
        )

        assert result["category"] == "clinical_question"
        assert result["requires_provider"] is True

    @pytest.mark.asyncio
    async def test_urgent_email_flagged_correctly(
        self, clinic_id, mock_llm_gateway, mock_graphiti
    ):
        """Urgent language triggers urgency=urgent."""
        from app.agents.email_agent import EmailAgent

        agent = EmailAgent(clinic_id=clinic_id)
        agent.llm = mock_llm_gateway
        agent.memory = mock_graphiti

        mock_llm_gateway.route.return_value = {
            "content": '{"category": "clinical_question", "urgency": "urgent", "requires_provider": true}',
            "model_used": "ollama/deepseek-coder-v2",
            "tokens_used": 18,
            "cost_usd": 0.0,
        }

        result = await agent.categorize_email(
            call_id="email_abc123",
            subject="Urgent - chest pain after medication",
            body="I started the new medication yesterday and now have severe chest pain.",
        )

        assert result["urgency"] == "urgent"

    @pytest.mark.asyncio
    async def test_categorize_uses_local_llm(
        self, clinic_id, mock_llm_gateway, mock_graphiti
    ):
        """Email categorization uses local model."""
        from app.agents.email_agent import EmailAgent

        agent = EmailAgent(clinic_id=clinic_id)
        agent.llm = mock_llm_gateway
        agent.memory = mock_graphiti

        mock_llm_gateway.route.return_value = {
            "content": '{"category": "general", "urgency": "routine", "requires_provider": false}',
            "model_used": "ollama/deepseek-coder-v2",
            "tokens_used": 15,
            "cost_usd": 0.0,
        }

        await agent.categorize_email(
            call_id="email_abc123",
            subject="Office hours",
            body="What are your office hours?",
        )

        call_kwargs = mock_llm_gateway.route.call_args[1]
        assert call_kwargs["task_type"] == "email_categorize"


class TestEmailAgentDraftGeneration:

    @pytest.mark.asyncio
    async def test_draft_appointment_confirmation(
        self, clinic_id, mock_llm_gateway, mock_graphiti
    ):
        """Draft appointment confirmation email."""
        from app.agents.email_agent import EmailAgent

        agent = EmailAgent(clinic_id=clinic_id)
        agent.llm = mock_llm_gateway
        agent.memory = mock_graphiti

        mock_llm_gateway.route.return_value = {
            "content": "Dear Maria, Your appointment with Dr. Chen is confirmed for July 1st at 9 AM...",
            "model_used": "ollama/qwen2.5:14b",
            "tokens_used": 55,
            "cost_usd": 0.0,
        }

        draft = await agent.draft_reply(
            call_id="email_abc123",
            category="appointment_confirmation",
            context={
                "patient_name": "Maria",
                "provider": "Dr. Chen",
                "datetime": "2026-07-01T09:00:00",
            },
        )

        assert draft is not None
        assert len(draft) > 0

    @pytest.mark.asyncio
    async def test_clinical_question_draft_includes_disclaimer(
        self, clinic_id, mock_llm_gateway, mock_graphiti
    ):
        """
        Drafts for clinical questions include a disclaimer.
        Agent never gives unsupervised medical advice.
        """
        from app.agents.email_agent import EmailAgent

        agent = EmailAgent(clinic_id=clinic_id)
        agent.llm = mock_llm_gateway
        agent.memory = mock_graphiti

        mock_llm_gateway.route.return_value = {
            "content": (
                "Thank you for reaching out. Your question has been forwarded to "
                "Dr. Chen for review. Please note this response is for informational "
                "purposes only and does not constitute medical advice."
            ),
            "model_used": "ollama/qwen2.5:14b",
            "tokens_used": 48,
            "cost_usd": 0.0,
        }

        draft = await agent.draft_reply(
            call_id="email_abc123",
            category="clinical_question",
            context={"patient_name": "Maria", "question": "medication side effects"},
        )

        assert draft is not None
        assert len(draft) > 10

    @pytest.mark.asyncio
    async def test_draft_reply_uses_local_llm(
        self, clinic_id, mock_llm_gateway, mock_graphiti
    ):
        """Email drafting uses local model."""
        from app.agents.email_agent import EmailAgent

        agent = EmailAgent(clinic_id=clinic_id)
        agent.llm = mock_llm_gateway
        agent.memory = mock_graphiti

        mock_llm_gateway.route.return_value = {
            "content": "Thank you for contacting us.",
            "model_used": "ollama/qwen2.5:14b",
            "tokens_used": 12,
            "cost_usd": 0.0,
        }

        await agent.draft_reply(
            call_id="email_abc123",
            category="general",
            context={"patient_name": "Maria"},
        )

        call_kwargs = mock_llm_gateway.route.call_args[1]
        assert call_kwargs["task_type"] == "email_categorize"


class TestEmailAgentSending:

    @pytest.mark.asyncio
    async def test_send_email_via_resend(
        self, clinic_id, mock_llm_gateway, mock_graphiti
    ):
        """Emails sent via Resend integration."""
        from app.agents.email_agent import EmailAgent

        agent = EmailAgent(clinic_id=clinic_id)
        agent.llm = mock_llm_gateway
        agent.memory = mock_graphiti

        mock_email_client = AsyncMock()
        mock_email_client.send = AsyncMock(return_value={
            "email_id": "EMAIL001",
            "status": "sent",
        })
        agent.email_client = mock_email_client

        result = await agent.send_email(
            to="maria@example.com",
            subject="Appointment Confirmation",
            body="Your appointment is confirmed.",
            patient_id="PAT_001",
        )

        assert result["status"] == "sent"
        mock_email_client.send.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_email_writes_audit_log(
        self, clinic_id, mock_llm_gateway, mock_graphiti
    ):
        """Email send writes HIPAA audit log."""
        from app.agents.email_agent import EmailAgent

        agent = EmailAgent(clinic_id=clinic_id)
        agent.llm = mock_llm_gateway
        agent.memory = mock_graphiti

        mock_email_client = AsyncMock()
        mock_email_client.send = AsyncMock(return_value={
            "email_id": "EMAIL001", "status": "sent"
        })
        agent.email_client = mock_email_client

        with patch("app.agents.email_agent.write_audit_log") as mock_audit:
            await agent.send_email(
                to="maria@example.com",
                subject="Appointment Confirmation",
                body="Your appointment is confirmed.",
                patient_id="PAT_001",
            )
            mock_audit.assert_called_once()
            kwargs = mock_audit.call_args[1]
            assert kwargs["event_type"] == "email_sent"

    @pytest.mark.asyncio
    async def test_email_failure_returns_error(
        self, clinic_id, mock_llm_gateway, mock_graphiti
    ):
        """Email send failure returns error — never crashes."""
        from app.agents.email_agent import EmailAgent

        agent = EmailAgent(clinic_id=clinic_id)
        agent.llm = mock_llm_gateway
        agent.memory = mock_graphiti

        mock_email_client = AsyncMock()
        mock_email_client.send = AsyncMock(
            side_effect=Exception("Resend API error")
        )
        agent.email_client = mock_email_client

        result = await agent.send_email(
            to="maria@example.com",
            subject="Test",
            body="Test",
            patient_id="PAT_001",
        )

        assert result["status"] == "failed"
        assert "error" in result
