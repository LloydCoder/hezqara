"""
Insurance Agent Tests — Sprint 4
TDD RED phase.

The Insurance Agent handles all payer-facing work:
  - Verify patient eligibility and benefits in real time
  - Check copay, deductible, out-of-pocket status
  - Identify in-network vs out-of-network providers
  - Communicate coverage to patient in plain language
  - Flag patients needing financial counselling
  - HIPAA audit log every coverage check
  - Store eligibility episode in Graphiti
"""
import pytest
from unittest.mock import AsyncMock, patch


class TestInsuranceAgentInitialisation:

    def test_insurance_agent_can_be_imported(self):
        from app.agents.insurance import InsuranceAgent
        assert InsuranceAgent is not None

    def test_insurance_agent_inherits_base_agent(self):
        from app.agents.insurance import InsuranceAgent
        from app.agents.base_agent import BaseAgent
        assert issubclass(InsuranceAgent, BaseAgent)

    def test_insurance_agent_requires_clinic_id(self):
        from app.agents.insurance import InsuranceAgent
        with pytest.raises(TypeError):
            InsuranceAgent()

    def test_insurance_agent_has_correct_type(self, clinic_id):
        from app.agents.insurance import InsuranceAgent
        agent = InsuranceAgent(clinic_id=clinic_id)
        assert agent.agent_type == "insurance"


class TestInsuranceAgentEligibilityVerification:

    @pytest.mark.asyncio
    async def test_verify_eligibility_returns_active_status(
        self, clinic_id, mock_llm_gateway, mock_graphiti
    ):
        """Active insurance returns eligible=True."""
        from app.agents.insurance import InsuranceAgent

        agent = InsuranceAgent(clinic_id=clinic_id)
        agent.llm = mock_llm_gateway
        agent.memory = mock_graphiti

        mock_insurance_client = AsyncMock()
        mock_insurance_client.check_eligibility = AsyncMock(return_value={
            "eligible": True,
            "carrier": "BlueCross BlueShield",
            "plan_type": "PPO",
            "effective_date": "2026-01-01",
            "termination_date": None,
        })
        agent.insurance_client = mock_insurance_client

        result = await agent.verify_eligibility(
            call_id="call_abc123",
            patient_id="PAT_001",
            member_id="BCB123456789",
            date_of_service="2026-07-01",
        )

        assert result["eligible"] is True
        assert result["carrier"] == "BlueCross BlueShield"

    @pytest.mark.asyncio
    async def test_verify_eligibility_returns_inactive_status(
        self, clinic_id, mock_llm_gateway, mock_graphiti
    ):
        """Terminated insurance returns eligible=False."""
        from app.agents.insurance import InsuranceAgent

        agent = InsuranceAgent(clinic_id=clinic_id)
        agent.llm = mock_llm_gateway
        agent.memory = mock_graphiti

        mock_insurance_client = AsyncMock()
        mock_insurance_client.check_eligibility = AsyncMock(return_value={
            "eligible": False,
            "carrier": "Aetna",
            "termination_date": "2026-03-31",
        })
        agent.insurance_client = mock_insurance_client

        result = await agent.verify_eligibility(
            call_id="call_abc123",
            patient_id="PAT_001",
            member_id="AET999",
            date_of_service="2026-07-01",
        )

        assert result["eligible"] is False

    @pytest.mark.asyncio
    async def test_verify_eligibility_api_failure_returns_error(
        self, clinic_id, mock_llm_gateway, mock_graphiti
    ):
        """API failure returns error — never crashes call."""
        from app.agents.insurance import InsuranceAgent

        agent = InsuranceAgent(clinic_id=clinic_id)
        agent.llm = mock_llm_gateway
        agent.memory = mock_graphiti

        mock_insurance_client = AsyncMock()
        mock_insurance_client.check_eligibility = AsyncMock(
            side_effect=Exception("Availity timeout")
        )
        agent.insurance_client = mock_insurance_client

        result = await agent.verify_eligibility(
            call_id="call_abc123",
            patient_id="PAT_001",
            member_id="BCB123",
            date_of_service="2026-07-01",
        )

        assert result["eligible"] is None
        assert "error" in result


class TestInsuranceAgentBenefitsCheck:

    @pytest.mark.asyncio
    async def test_get_benefits_returns_copay_deductible(
        self, clinic_id, mock_llm_gateway, mock_graphiti
    ):
        """Benefits check returns copay and deductible amounts."""
        from app.agents.insurance import InsuranceAgent

        agent = InsuranceAgent(clinic_id=clinic_id)
        agent.llm = mock_llm_gateway
        agent.memory = mock_graphiti

        mock_insurance_client = AsyncMock()
        mock_insurance_client.get_benefits = AsyncMock(return_value={
            "copay_primary_care": 30,
            "copay_specialist": 60,
            "deductible_annual": 1500,
            "deductible_met": 450,
            "deductible_remaining": 1050,
            "out_of_pocket_max": 5000,
            "out_of_pocket_met": 450,
        })
        agent.insurance_client = mock_insurance_client

        result = await agent.get_benefits(
            call_id="call_abc123",
            member_id="BCB123456789",
            service_type="primary_care",
        )

        assert result["copay_primary_care"] == 30
        assert result["deductible_remaining"] == 1050

    @pytest.mark.asyncio
    async def test_check_in_network_provider(
        self, clinic_id, mock_llm_gateway, mock_graphiti
    ):
        """Confirms whether provider is in-network for this plan."""
        from app.agents.insurance import InsuranceAgent

        agent = InsuranceAgent(clinic_id=clinic_id)
        agent.llm = mock_llm_gateway
        agent.memory = mock_graphiti

        mock_insurance_client = AsyncMock()
        mock_insurance_client.check_network_status = AsyncMock(return_value={
            "in_network": True,
            "provider_id": "P001",
            "network_name": "BlueCross PPO Network",
        })
        agent.insurance_client = mock_insurance_client

        result = await agent.check_network_status(
            call_id="call_abc123",
            provider_id="P001",
            member_id="BCB123456789",
        )

        assert result["in_network"] is True


class TestInsuranceAgentPatientCommunication:

    @pytest.mark.asyncio
    async def test_explain_coverage_uses_plain_language(
        self, clinic_id, mock_llm_gateway, mock_graphiti
    ):
        """
        Coverage explanation for patient is in plain language.
        Uses local LLM — routine summarization.
        """
        from app.agents.insurance import InsuranceAgent

        agent = InsuranceAgent(clinic_id=clinic_id)
        agent.llm = mock_llm_gateway
        agent.memory = mock_graphiti

        mock_llm_gateway.route.return_value = {
            "content": (
                "Your insurance is active. For today's visit, "
                "your copay is $30. You have $1,050 left on your deductible."
            ),
            "model_used": "ollama/qwen2.5:14b",
            "tokens_used": 38,
            "cost_usd": 0.0,
        }

        benefits = {
            "copay_primary_care": 30,
            "deductible_remaining": 1050,
            "eligible": True,
        }

        explanation = await agent.explain_coverage_to_patient(
            call_id="call_abc123",
            benefits=benefits,
        )

        assert explanation is not None
        assert len(explanation) > 0
        call_kwargs = mock_llm_gateway.route.call_args[1]
        assert call_kwargs["task_type"] == "insurance_code_lookup"

    @pytest.mark.asyncio
    async def test_flag_financial_counselling_needed(
        self, clinic_id, mock_llm_gateway, mock_graphiti
    ):
        """
        Uninsured or high out-of-pocket patients are flagged
        for financial counselling.
        """
        from app.agents.insurance import InsuranceAgent

        agent = InsuranceAgent(clinic_id=clinic_id)
        agent.llm = mock_llm_gateway
        agent.memory = mock_graphiti

        result = agent.assess_financial_counselling_need(
            benefits={"eligible": False, "uninsured": True},
        )

        assert result["needs_counselling"] is True
        assert result["reason"] is not None


class TestInsuranceAgentHIPAACompliance:

    @pytest.mark.asyncio
    async def test_eligibility_check_writes_audit_log(
        self, clinic_id, mock_llm_gateway, mock_graphiti
    ):
        """Every eligibility check writes to HIPAA audit log."""
        from app.agents.insurance import InsuranceAgent

        agent = InsuranceAgent(clinic_id=clinic_id)
        agent.llm = mock_llm_gateway
        agent.memory = mock_graphiti

        mock_insurance_client = AsyncMock()
        mock_insurance_client.check_eligibility = AsyncMock(return_value={
            "eligible": True, "carrier": "BlueCross"
        })
        agent.insurance_client = mock_insurance_client

        with patch("app.agents.insurance.write_audit_log") as mock_audit:
            await agent.verify_eligibility(
                call_id="call_abc123",
                patient_id="PAT_001",
                member_id="BCB123",
                date_of_service="2026-07-01",
            )
            mock_audit.assert_called_once()
            kwargs = mock_audit.call_args[1]
            assert kwargs["event_type"] == "eligibility_checked"
            assert kwargs["clinic_id"] == clinic_id

    @pytest.mark.asyncio
    async def test_eligibility_stores_graphiti_episode(
        self, clinic_id, mock_llm_gateway, mock_graphiti
    ):
        """Eligibility result stored in Graphiti for prior auth agent."""
        from app.agents.insurance import InsuranceAgent

        agent = InsuranceAgent(clinic_id=clinic_id)
        agent.llm = mock_llm_gateway
        agent.memory = mock_graphiti

        mock_insurance_client = AsyncMock()
        mock_insurance_client.check_eligibility = AsyncMock(return_value={
            "eligible": True, "carrier": "Aetna"
        })
        agent.insurance_client = mock_insurance_client

        await agent.verify_eligibility(
            call_id="call_abc123",
            patient_id="PAT_001",
            member_id="AET001",
            date_of_service="2026-07-01",
        )

        mock_graphiti.add_episode.assert_called_once()
        kwargs = mock_graphiti.add_episode.call_args[1]
        assert kwargs["clinic_id"] == clinic_id
        assert kwargs["patient_id"] == "PAT_001"
