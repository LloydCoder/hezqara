"""
Prior Auth Agent Tests — Sprint 5
TDD RED phase.

Prior authorization is the #1 revenue cycle problem for clinics.
CMS-0057-F mandates decision within 72 hours (Jan 2027).

Responsibilities:
  - Determine if a service/medication requires prior auth
  - Collect clinical documentation for the request
  - Submit PA request to payer via FHIR Da Vinci PAS
  - Poll for payer decision (approved/denied/pending)
  - Notify clinic and patient of outcome
  - Handle peer-to-peer review requests
  - Parliament Ensemble vote for complex clinical reasoning
  - HIPAA audit log every PA action
"""
import pytest
from unittest.mock import AsyncMock, patch


class TestPriorAuthAgentInitialisation:

    def test_prior_auth_agent_can_be_imported(self):
        from app.agents.prior_auth import PriorAuthAgent
        assert PriorAuthAgent is not None

    def test_prior_auth_agent_inherits_base_agent(self):
        from app.agents.prior_auth import PriorAuthAgent
        from app.agents.base_agent import BaseAgent
        assert issubclass(PriorAuthAgent, BaseAgent)

    def test_prior_auth_agent_requires_clinic_id(self):
        from app.agents.prior_auth import PriorAuthAgent
        with pytest.raises(TypeError):
            PriorAuthAgent()

    def test_prior_auth_agent_has_correct_type(self, clinic_id):
        from app.agents.prior_auth import PriorAuthAgent
        agent = PriorAuthAgent(clinic_id=clinic_id)
        assert agent.agent_type == "prior_auth"


class TestPriorAuthRequirementCheck:

    @pytest.mark.asyncio
    async def test_service_requires_prior_auth_returns_true(
        self, clinic_id, mock_llm_gateway, mock_graphiti
    ):
        """MRI requires prior auth — returns True."""
        from app.agents.prior_auth import PriorAuthAgent

        agent = PriorAuthAgent(clinic_id=clinic_id)
        agent.llm = mock_llm_gateway
        agent.memory = mock_graphiti

        mock_insurance_client = AsyncMock()
        mock_insurance_client.check_pa_requirement = AsyncMock(return_value={
            "required": True,
            "service_code": "70553",
            "reason": "MRI Brain with contrast requires PA",
        })
        agent.insurance_client = mock_insurance_client

        result = await agent.check_pa_requirement(
            call_id="call_abc123",
            service_code="70553",
            member_id="BCB123",
            diagnosis_code="G35",
        )

        assert result["required"] is True

    @pytest.mark.asyncio
    async def test_routine_service_does_not_require_prior_auth(
        self, clinic_id, mock_llm_gateway, mock_graphiti
    ):
        """Annual checkup does not require prior auth."""
        from app.agents.prior_auth import PriorAuthAgent

        agent = PriorAuthAgent(clinic_id=clinic_id)
        agent.llm = mock_llm_gateway
        agent.memory = mock_graphiti

        mock_insurance_client = AsyncMock()
        mock_insurance_client.check_pa_requirement = AsyncMock(return_value={
            "required": False,
            "service_code": "99213",
        })
        agent.insurance_client = mock_insurance_client

        result = await agent.check_pa_requirement(
            call_id="call_abc123",
            service_code="99213",
            member_id="BCB123",
            diagnosis_code="Z00.00",
        )

        assert result["required"] is False


class TestPriorAuthSubmission:

    @pytest.mark.asyncio
    async def test_submit_pa_request_returns_tracking_number(
        self, clinic_id, mock_llm_gateway, mock_graphiti
    ):
        """PA submission returns a payer tracking number."""
        from app.agents.prior_auth import PriorAuthAgent

        agent = PriorAuthAgent(clinic_id=clinic_id)
        agent.llm = mock_llm_gateway
        agent.memory = mock_graphiti

        mock_payer_client = AsyncMock()
        mock_payer_client.submit_prior_auth = AsyncMock(return_value={
            "tracking_number": "PA-2026-00123",
            "status": "pending",
            "submitted_at": "2026-07-01T10:00:00Z",
        })
        agent.payer_client = mock_payer_client

        pa_data = {
            "patient_id": "PAT_001",
            "service_code": "70553",
            "diagnosis_codes": ["G35"],
            "clinical_notes": "Patient presenting with MS symptoms.",
            "provider_id": "P001",
        }

        result = await agent.submit_pa_request(
            call_id="call_abc123",
            pa_data=pa_data,
        )

        assert result["success"] is True
        assert "tracking_number" in result
        assert result["status"] == "pending"

    @pytest.mark.asyncio
    async def test_submit_pa_payer_failure_returns_error(
        self, clinic_id, mock_llm_gateway, mock_graphiti
    ):
        """Payer API failure returns error — never crashes."""
        from app.agents.prior_auth import PriorAuthAgent

        agent = PriorAuthAgent(clinic_id=clinic_id)
        agent.llm = mock_llm_gateway
        agent.memory = mock_graphiti

        mock_payer_client = AsyncMock()
        mock_payer_client.submit_prior_auth = AsyncMock(
            side_effect=Exception("Payer portal down")
        )
        agent.payer_client = mock_payer_client

        result = await agent.submit_pa_request(
            call_id="call_abc123",
            pa_data={"patient_id": "PAT_001", "service_code": "70553"},
        )

        assert result["success"] is False
        assert "error" in result

    @pytest.mark.asyncio
    async def test_submit_pa_writes_audit_log(
        self, clinic_id, mock_llm_gateway, mock_graphiti
    ):
        """PA submission writes HIPAA audit log."""
        from app.agents.prior_auth import PriorAuthAgent

        agent = PriorAuthAgent(clinic_id=clinic_id)
        agent.llm = mock_llm_gateway
        agent.memory = mock_graphiti

        mock_payer_client = AsyncMock()
        mock_payer_client.submit_prior_auth = AsyncMock(return_value={
            "tracking_number": "PA-001",
            "status": "pending",
        })
        agent.payer_client = mock_payer_client

        with patch("app.agents.prior_auth.write_audit_log") as mock_audit:
            await agent.submit_pa_request(
                call_id="call_abc123",
                pa_data={"patient_id": "PAT_001", "service_code": "70553"},
            )
            mock_audit.assert_called_once()
            kwargs = mock_audit.call_args[1]
            assert kwargs["event_type"] == "prior_auth_submitted"

    @pytest.mark.asyncio
    async def test_submit_pa_stores_graphiti_episode(
        self, clinic_id, mock_llm_gateway, mock_graphiti
    ):
        """PA submission stored in Graphiti for status polling."""
        from app.agents.prior_auth import PriorAuthAgent

        agent = PriorAuthAgent(clinic_id=clinic_id)
        agent.llm = mock_llm_gateway
        agent.memory = mock_graphiti

        mock_payer_client = AsyncMock()
        mock_payer_client.submit_prior_auth = AsyncMock(return_value={
            "tracking_number": "PA-001",
            "status": "pending",
        })
        agent.payer_client = mock_payer_client

        await agent.submit_pa_request(
            call_id="call_abc123",
            pa_data={"patient_id": "PAT_001", "service_code": "70553"},
        )

        mock_graphiti.add_episode.assert_called_once()


class TestPriorAuthStatusPolling:

    @pytest.mark.asyncio
    async def test_check_pa_status_returns_approved(
        self, clinic_id, mock_llm_gateway, mock_graphiti
    ):
        """Status check returns approved when payer approves."""
        from app.agents.prior_auth import PriorAuthAgent

        agent = PriorAuthAgent(clinic_id=clinic_id)
        agent.llm = mock_llm_gateway
        agent.memory = mock_graphiti

        mock_payer_client = AsyncMock()
        mock_payer_client.get_pa_status = AsyncMock(return_value={
            "status": "approved",
            "tracking_number": "PA-001",
            "approved_units": 1,
            "valid_from": "2026-07-01",
            "valid_until": "2026-12-31",
        })
        agent.payer_client = mock_payer_client

        result = await agent.check_pa_status(
            call_id="call_abc123",
            tracking_number="PA-001",
        )

        assert result["status"] == "approved"

    @pytest.mark.asyncio
    async def test_check_pa_status_returns_denied(
        self, clinic_id, mock_llm_gateway, mock_graphiti
    ):
        """Status check returns denied with reason."""
        from app.agents.prior_auth import PriorAuthAgent

        agent = PriorAuthAgent(clinic_id=clinic_id)
        agent.llm = mock_llm_gateway
        agent.memory = mock_graphiti

        mock_payer_client = AsyncMock()
        mock_payer_client.get_pa_status = AsyncMock(return_value={
            "status": "denied",
            "tracking_number": "PA-001",
            "denial_reason": "Medical necessity not established",
        })
        agent.payer_client = mock_payer_client

        result = await agent.check_pa_status(
            call_id="call_abc123",
            tracking_number="PA-001",
        )

        assert result["status"] == "denied"
        assert "denial_reason" in result


class TestPriorAuthClinicalReasoning:

    @pytest.mark.asyncio
    async def test_complex_pa_routes_to_parliament(
        self, clinic_id, mock_llm_gateway, mock_graphiti
    ):
        """
        Complex PA clinical reasoning routes to Parliament Ensemble
        — never to a local model.
        """
        from app.agents.prior_auth import PriorAuthAgent

        agent = PriorAuthAgent(clinic_id=clinic_id)
        agent.llm = mock_llm_gateway
        agent.memory = mock_graphiti

        mock_llm_gateway.route.return_value = {
            "content": '{"recommendation": "approve", "clinical_basis": "RRMS criteria met"}',
            "model_used": "claude-sonnet-4-6",
            "tokens_used": 245,
            "cost_usd": 0.008,
        }

        result = await agent.generate_clinical_justification(
            call_id="call_abc123",
            service_code="70553",
            diagnosis_codes=["G35"],
            clinical_notes="Relapsing-remitting MS confirmed by prior MRI.",
        )

        assert result is not None
        call_kwargs = mock_llm_gateway.route.call_args[1]
        assert call_kwargs["task_type"] == "prior_auth_clinical"
