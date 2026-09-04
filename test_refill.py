"""
Refill Agent Tests — Sprint 10
TDD RED phase.

The Refill Agent handles medication refill requests end-to-end.

Responsibilities:
  - Parse medication name, dose, pharmacy from speech
  - Look up prescription in EHR
  - Check refill eligibility (too early, controlled substance)
  - Route to provider for approval if needed
  - Send refill to pharmacy electronically
  - Notify patient of outcome via SMS
  - HIPAA audit log every refill action
"""
import pytest
from unittest.mock import AsyncMock, patch


class TestRefillAgentInitialisation:

    def test_refill_agent_can_be_imported(self):
        from app.agents.refill import RefillAgent
        assert RefillAgent is not None

    def test_refill_agent_inherits_base_agent(self):
        from app.agents.refill import RefillAgent
        from app.agents.base_agent import BaseAgent
        assert issubclass(RefillAgent, BaseAgent)

    def test_refill_agent_requires_clinic_id(self):
        from app.agents.refill import RefillAgent
        with pytest.raises(TypeError):
            RefillAgent()

    def test_refill_agent_has_correct_type(self, clinic_id):
        from app.agents.refill import RefillAgent
        agent = RefillAgent(clinic_id=clinic_id)
        assert agent.agent_type == "refill"


class TestRefillAgentMedicationExtraction:

    @pytest.mark.asyncio
    async def test_extract_medication_from_utterance(
        self, clinic_id, mock_llm_gateway, mock_graphiti
    ):
        """Extracts medication name, dose, and pharmacy from speech."""
        from app.agents.refill import RefillAgent

        agent = RefillAgent(clinic_id=clinic_id)
        agent.llm = mock_llm_gateway
        agent.memory = mock_graphiti

        mock_llm_gateway.route.return_value = {
            "content": (
                '{"medication": "Lisinopril", "dose": "10mg", '
                '"pharmacy": "CVS on Main Street", "days_supply": 30}'
            ),
            "model_used": "ollama/deepseek-coder-v2",
            "tokens_used": 28,
            "cost_usd": 0.0,
        }

        result = await agent.extract_refill_request(
            call_id="call_abc123",
            utterance="I need a refill on my Lisinopril 10mg, I usually go to CVS on Main Street",
        )

        assert result["medication"] == "Lisinopril"
        assert result["dose"] == "10mg"
        assert "CVS" in result["pharmacy"]

    @pytest.mark.asyncio
    async def test_extract_refill_uses_local_llm(
        self, clinic_id, mock_llm_gateway, mock_graphiti
    ):
        """Refill extraction uses local model — never Claude."""
        from app.agents.refill import RefillAgent

        agent = RefillAgent(clinic_id=clinic_id)
        agent.llm = mock_llm_gateway
        agent.memory = mock_graphiti

        mock_llm_gateway.route.return_value = {
            "content": '{"medication": "Metformin", "dose": "500mg"}',
            "model_used": "ollama/deepseek-coder-v2",
            "tokens_used": 18,
            "cost_usd": 0.0,
        }

        await agent.extract_refill_request(
            call_id="call_abc123",
            utterance="Metformin 500mg please",
        )

        call_kwargs = mock_llm_gateway.route.call_args[1]
        assert call_kwargs["task_type"] == "refill_request_parse"


class TestRefillAgentEligibilityCheck:

    @pytest.mark.asyncio
    async def test_eligible_refill_returns_approved(
        self, clinic_id, mock_llm_gateway, mock_graphiti, mock_ehr_client
    ):
        """Eligible refill returns eligible=True."""
        from app.agents.refill import RefillAgent

        agent = RefillAgent(clinic_id=clinic_id)
        agent.llm = mock_llm_gateway
        agent.memory = mock_graphiti
        agent.ehr = mock_ehr_client

        mock_ehr_client.check_refill_eligibility = AsyncMock(return_value={
            "eligible": True,
            "refills_remaining": 3,
            "last_filled": "2026-06-01",
            "controlled_substance": False,
        })

        result = await agent.check_refill_eligibility(
            call_id="call_abc123",
            patient_id="PAT_001",
            medication="Lisinopril",
        )

        assert result["eligible"] is True
        assert result["refills_remaining"] == 3

    @pytest.mark.asyncio
    async def test_too_early_refill_returns_ineligible(
        self, clinic_id, mock_llm_gateway, mock_graphiti, mock_ehr_client
    ):
        """Too-early refill request returns eligible=False with reason."""
        from app.agents.refill import RefillAgent

        agent = RefillAgent(clinic_id=clinic_id)
        agent.llm = mock_llm_gateway
        agent.memory = mock_graphiti
        agent.ehr = mock_ehr_client

        mock_ehr_client.check_refill_eligibility = AsyncMock(return_value={
            "eligible": False,
            "reason": "too_early",
            "eligible_date": "2026-07-15",
            "controlled_substance": False,
        })

        result = await agent.check_refill_eligibility(
            call_id="call_abc123",
            patient_id="PAT_001",
            medication="Lisinopril",
        )

        assert result["eligible"] is False
        assert result["reason"] == "too_early"

    @pytest.mark.asyncio
    async def test_controlled_substance_routes_to_provider(
        self, clinic_id, mock_llm_gateway, mock_graphiti, mock_ehr_client
    ):
        """
        Controlled substance refill always requires provider approval.
        Never auto-approved.
        """
        from app.agents.refill import RefillAgent

        agent = RefillAgent(clinic_id=clinic_id)
        agent.llm = mock_llm_gateway
        agent.memory = mock_graphiti
        agent.ehr = mock_ehr_client

        mock_ehr_client.check_refill_eligibility = AsyncMock(return_value={
            "eligible": True,
            "controlled_substance": True,
            "schedule": "II",
        })

        result = await agent.check_refill_eligibility(
            call_id="call_abc123",
            patient_id="PAT_001",
            medication="Adderall",
        )

        assert result["requires_provider_approval"] is True


class TestRefillAgentProcessing:

    @pytest.mark.asyncio
    async def test_process_refill_sends_to_pharmacy(
        self, clinic_id, mock_llm_gateway, mock_graphiti, mock_ehr_client
    ):
        """Approved refill is sent to pharmacy electronically."""
        from app.agents.refill import RefillAgent

        agent = RefillAgent(clinic_id=clinic_id)
        agent.llm = mock_llm_gateway
        agent.memory = mock_graphiti
        agent.ehr = mock_ehr_client

        mock_ehr_client.send_refill_to_pharmacy = AsyncMock(return_value={
            "refill_id": "RX001",
            "status": "sent",
            "pharmacy": "CVS Main Street",
            "estimated_ready": "2026-07-01T18:00:00",
        })

        result = await agent.process_refill(
            call_id="call_abc123",
            patient_id="PAT_001",
            medication="Lisinopril",
            dose="10mg",
            pharmacy="CVS Main Street",
        )

        assert result["success"] is True
        assert result["status"] == "sent"
        mock_ehr_client.send_refill_to_pharmacy.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_refill_writes_audit_log(
        self, clinic_id, mock_llm_gateway, mock_graphiti, mock_ehr_client
    ):
        """Every refill processed writes HIPAA audit log."""
        from app.agents.refill import RefillAgent

        agent = RefillAgent(clinic_id=clinic_id)
        agent.llm = mock_llm_gateway
        agent.memory = mock_graphiti
        agent.ehr = mock_ehr_client

        mock_ehr_client.send_refill_to_pharmacy = AsyncMock(return_value={
            "refill_id": "RX001", "status": "sent"
        })

        with patch("app.agents.refill.write_audit_log") as mock_audit:
            await agent.process_refill(
                call_id="call_abc123",
                patient_id="PAT_001",
                medication="Lisinopril",
                dose="10mg",
                pharmacy="CVS",
            )
            mock_audit.assert_called_once()
            kwargs = mock_audit.call_args[1]
            assert kwargs["event_type"] == "refill_processed"
            assert kwargs["clinic_id"] == clinic_id

    @pytest.mark.asyncio
    async def test_process_refill_stores_graphiti_episode(
        self, clinic_id, mock_llm_gateway, mock_graphiti, mock_ehr_client
    ):
        """Refill stored in Graphiti — recall agent knows medication history."""
        from app.agents.refill import RefillAgent

        agent = RefillAgent(clinic_id=clinic_id)
        agent.llm = mock_llm_gateway
        agent.memory = mock_graphiti
        agent.ehr = mock_ehr_client

        mock_ehr_client.send_refill_to_pharmacy = AsyncMock(return_value={
            "refill_id": "RX001", "status": "sent"
        })

        await agent.process_refill(
            call_id="call_abc123",
            patient_id="PAT_001",
            medication="Lisinopril",
            dose="10mg",
            pharmacy="CVS",
        )

        mock_graphiti.add_episode.assert_called_once()
        kwargs = mock_graphiti.add_episode.call_args[1]
        assert kwargs["clinic_id"] == clinic_id
        assert kwargs["patient_id"] == "PAT_001"

    @pytest.mark.asyncio
    async def test_pharmacy_failure_returns_error(
        self, clinic_id, mock_llm_gateway, mock_graphiti, mock_ehr_client
    ):
        """Pharmacy send failure returns error — never crashes call."""
        from app.agents.refill import RefillAgent

        agent = RefillAgent(clinic_id=clinic_id)
        agent.llm = mock_llm_gateway
        agent.memory = mock_graphiti
        agent.ehr = mock_ehr_client

        mock_ehr_client.send_refill_to_pharmacy = AsyncMock(
            side_effect=Exception("Pharmacy network error")
        )

        result = await agent.process_refill(
            call_id="call_abc123",
            patient_id="PAT_001",
            medication="Lisinopril",
            dose="10mg",
            pharmacy="CVS",
        )

        assert result["success"] is False
        assert "error" in result

    @pytest.mark.asyncio
    async def test_generate_refill_confirmation_uses_local_llm(
        self, clinic_id, mock_llm_gateway, mock_graphiti
    ):
        """Confirmation message uses local model."""
        from app.agents.refill import RefillAgent

        agent = RefillAgent(clinic_id=clinic_id)
        agent.llm = mock_llm_gateway
        agent.memory = mock_graphiti

        mock_llm_gateway.route.return_value = {
            "content": "Your Lisinopril refill has been sent to CVS. Ready by 6 PM today.",
            "model_used": "ollama/qwen2.5:14b",
            "tokens_used": 22,
            "cost_usd": 0.0,
        }

        msg = await agent.generate_refill_confirmation(
            medication="Lisinopril",
            pharmacy="CVS Main Street",
            estimated_ready="2026-07-01T18:00:00",
        )

        assert msg is not None
        call_kwargs = mock_llm_gateway.route.call_args[1]
        assert call_kwargs["task_type"] == "refill_request_parse"
