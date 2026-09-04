"""
Referrals Agent Tests — Sprint 12
TDD RED phase.

Manages specialist referral end-to-end:
  - Capture referral reason and specialty from speech
  - Find in-network specialists
  - Create referral packet in EHR
  - Track referral status
  - Follow up when referral goes stale
  - HIPAA audit log every referral action
"""
import pytest
from unittest.mock import AsyncMock, patch


class TestReferralsAgentInitialisation:

    def test_referrals_agent_can_be_imported(self):
        from app.agents.referrals import ReferralsAgent
        assert ReferralsAgent is not None

    def test_referrals_agent_inherits_base_agent(self):
        from app.agents.referrals import ReferralsAgent
        from app.agents.base_agent import BaseAgent
        assert issubclass(ReferralsAgent, BaseAgent)

    def test_referrals_agent_requires_clinic_id(self):
        from app.agents.referrals import ReferralsAgent
        with pytest.raises(TypeError):
            ReferralsAgent()

    def test_referrals_agent_has_correct_type(self, clinic_id):
        from app.agents.referrals import ReferralsAgent
        agent = ReferralsAgent(clinic_id=clinic_id)
        assert agent.agent_type == "referrals"


class TestReferralsAgentExtraction:

    @pytest.mark.asyncio
    async def test_extract_referral_details_from_utterance(
        self, clinic_id, mock_llm_gateway, mock_graphiti
    ):
        """Extracts specialty, reason, and urgency from speech."""
        from app.agents.referrals import ReferralsAgent

        agent = ReferralsAgent(clinic_id=clinic_id)
        agent.llm = mock_llm_gateway
        agent.memory = mock_graphiti

        mock_llm_gateway.route.return_value = {
            "content": (
                '{"specialty": "cardiology", "reason": "chest pain evaluation", '
                '"urgency": "routine", "referring_provider": "P001"}'
            ),
            "model_used": "ollama/deepseek-coder-v2",
            "tokens_used": 28,
            "cost_usd": 0.0,
        }

        result = await agent.extract_referral_details(
            call_id="call_abc123",
            utterance="Dr. Chen wants me to see a cardiologist about my chest pain",
        )

        assert result["specialty"] == "cardiology"
        assert result["urgency"] == "routine"

    @pytest.mark.asyncio
    async def test_urgent_referral_detected(
        self, clinic_id, mock_llm_gateway, mock_graphiti
    ):
        """Urgent language triggers urgency=urgent."""
        from app.agents.referrals import ReferralsAgent

        agent = ReferralsAgent(clinic_id=clinic_id)
        agent.llm = mock_llm_gateway
        agent.memory = mock_graphiti

        mock_llm_gateway.route.return_value = {
            "content": '{"specialty": "oncology", "urgency": "urgent", "reason": "suspicious mass"}',
            "model_used": "ollama/deepseek-coder-v2",
            "tokens_used": 20,
            "cost_usd": 0.0,
        }

        result = await agent.extract_referral_details(
            call_id="call_abc123",
            utterance="I was told I need to see an oncologist urgently",
        )

        assert result["urgency"] == "urgent"


class TestReferralsAgentCreation:

    @pytest.mark.asyncio
    async def test_create_referral_returns_referral_id(
        self, clinic_id, mock_llm_gateway, mock_graphiti, mock_ehr_client
    ):
        """Referral creation returns referral_id."""
        from app.agents.referrals import ReferralsAgent

        agent = ReferralsAgent(clinic_id=clinic_id)
        agent.llm = mock_llm_gateway
        agent.memory = mock_graphiti
        agent.ehr = mock_ehr_client

        mock_ehr_client.create_referral = AsyncMock(return_value={
            "referral_id": "REF001",
            "status": "initiated",
            "specialist": "Dr. Johnson",
        })

        result = await agent.create_referral(
            call_id="call_abc123",
            patient_id="PAT_001",
            specialty="cardiology",
            reason="chest pain evaluation",
            urgency="routine",
            referring_provider_id="P001",
        )

        assert result["success"] is True
        assert result["referral_id"] == "REF001"

    @pytest.mark.asyncio
    async def test_create_referral_writes_audit_log(
        self, clinic_id, mock_llm_gateway, mock_graphiti, mock_ehr_client
    ):
        """Referral creation writes HIPAA audit log."""
        from app.agents.referrals import ReferralsAgent

        agent = ReferralsAgent(clinic_id=clinic_id)
        agent.llm = mock_llm_gateway
        agent.memory = mock_graphiti
        agent.ehr = mock_ehr_client

        mock_ehr_client.create_referral = AsyncMock(return_value={
            "referral_id": "REF001", "status": "initiated"
        })

        with patch("app.agents.referrals.write_audit_log") as mock_audit:
            await agent.create_referral(
                call_id="call_abc123",
                patient_id="PAT_001",
                specialty="cardiology",
                reason="chest pain",
                urgency="routine",
                referring_provider_id="P001",
            )
            mock_audit.assert_called_once()
            kwargs = mock_audit.call_args[1]
            assert kwargs["event_type"] == "referral_created"

    @pytest.mark.asyncio
    async def test_create_referral_stores_graphiti_episode(
        self, clinic_id, mock_llm_gateway, mock_graphiti, mock_ehr_client
    ):
        """Referral stored in Graphiti for tracking."""
        from app.agents.referrals import ReferralsAgent

        agent = ReferralsAgent(clinic_id=clinic_id)
        agent.llm = mock_llm_gateway
        agent.memory = mock_graphiti
        agent.ehr = mock_ehr_client

        mock_ehr_client.create_referral = AsyncMock(return_value={
            "referral_id": "REF001", "status": "initiated"
        })

        await agent.create_referral(
            call_id="call_abc123",
            patient_id="PAT_001",
            specialty="cardiology",
            reason="chest pain",
            urgency="routine",
            referring_provider_id="P001",
        )

        mock_graphiti.add_episode.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_referral_ehr_failure_returns_error(
        self, clinic_id, mock_llm_gateway, mock_graphiti, mock_ehr_client
    ):
        """EHR failure returns error — never crashes."""
        from app.agents.referrals import ReferralsAgent

        agent = ReferralsAgent(clinic_id=clinic_id)
        agent.llm = mock_llm_gateway
        agent.memory = mock_graphiti
        agent.ehr = mock_ehr_client

        mock_ehr_client.create_referral = AsyncMock(
            side_effect=Exception("EHR timeout")
        )

        result = await agent.create_referral(
            call_id="call_abc123",
            patient_id="PAT_001",
            specialty="cardiology",
            reason="chest pain",
            urgency="routine",
            referring_provider_id="P001",
        )

        assert result["success"] is False
        assert "error" in result


class TestReferralsAgentStatusTracking:

    @pytest.mark.asyncio
    async def test_check_referral_status_returns_status(
        self, clinic_id, mock_llm_gateway, mock_graphiti, mock_ehr_client
    ):
        """Status check returns current referral status."""
        from app.agents.referrals import ReferralsAgent

        agent = ReferralsAgent(clinic_id=clinic_id)
        agent.llm = mock_llm_gateway
        agent.memory = mock_graphiti
        agent.ehr = mock_ehr_client

        mock_ehr_client.get_referral_status = AsyncMock(return_value={
            "referral_id": "REF001",
            "status": "scheduled",
            "appointment_date": "2026-07-15",
            "specialist": "Dr. Johnson",
        })

        result = await agent.check_referral_status(
            call_id="call_abc123",
            referral_id="REF001",
        )

        assert result["status"] == "scheduled"
        assert result["appointment_date"] == "2026-07-15"
