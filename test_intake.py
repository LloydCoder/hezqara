"""
Intake Agent Tests — Sprint 3
TDD RED phase: all tests written before implementation exists.

The Intake Agent collects patient information before their visit.
It runs between scheduling and the appointment itself.

Responsibilities:
  - Collect demographics (name, DOB, address, phone, email)
  - Collect insurance information (carrier, member ID, group number)
  - Collect medical history (current medications, allergies, conditions)
  - Collect reason for visit and symptoms
  - Validate collected data for completeness
  - Write patient data back to EHR
  - Generate intake summary for provider
  - HIPAA audit log on every PHI collection
  - Store intake episode in Graphiti
"""
import pytest
from unittest.mock import AsyncMock, patch


class TestIntakeAgentInitialisation:
    """Agent must initialise correctly."""

    def test_intake_agent_can_be_imported(self):
        from app.agents.intake import IntakeAgent
        assert IntakeAgent is not None

    def test_intake_agent_inherits_base_agent(self):
        from app.agents.intake import IntakeAgent
        from app.agents.base_agent import BaseAgent
        assert issubclass(IntakeAgent, BaseAgent)

    def test_intake_agent_requires_clinic_id(self):
        from app.agents.intake import IntakeAgent
        with pytest.raises(TypeError):
            IntakeAgent()

    def test_intake_agent_has_correct_type(self, clinic_id):
        from app.agents.intake import IntakeAgent
        agent = IntakeAgent(clinic_id=clinic_id)
        assert agent.agent_type == "intake"

    def test_intake_agent_stores_clinic_id(self, clinic_id):
        from app.agents.intake import IntakeAgent
        agent = IntakeAgent(clinic_id=clinic_id)
        assert agent.clinic_id == clinic_id


class TestIntakeAgentDemographicsCollection:
    """Patient demographics collection from voice."""

    @pytest.mark.asyncio
    async def test_extract_date_of_birth_from_utterance(
        self, clinic_id, mock_llm_gateway, mock_graphiti
    ):
        """
        Extracts date of birth from natural speech.
        Multiple formats supported.
        """
        from app.agents.intake import IntakeAgent

        agent = IntakeAgent(clinic_id=clinic_id)
        agent.llm = mock_llm_gateway
        agent.memory = mock_graphiti

        mock_llm_gateway.route.return_value = {
            "content": '{"date_of_birth": "1985-03-15"}',
            "model_used": "ollama/deepseek-coder-v2",
            "tokens_used": 14,
            "cost_usd": 0.0,
        }

        result = await agent.extract_date_of_birth(
            call_id="call_abc123",
            utterance="My birthday is March 15th, 1985",
        )

        assert result["date_of_birth"] == "1985-03-15"

    @pytest.mark.asyncio
    async def test_extract_address_from_utterance(
        self, clinic_id, mock_llm_gateway, mock_graphiti
    ):
        """Extracts street address, city, state, zip from speech."""
        from app.agents.intake import IntakeAgent

        agent = IntakeAgent(clinic_id=clinic_id)
        agent.llm = mock_llm_gateway
        agent.memory = mock_graphiti

        mock_llm_gateway.route.return_value = {
            "content": (
                '{"street": "123 Main Street", "city": "Brooklyn", '
                '"state": "NY", "zip": "11201"}'
            ),
            "model_used": "ollama/deepseek-coder-v2",
            "tokens_used": 28,
            "cost_usd": 0.0,
        }

        result = await agent.extract_address(
            call_id="call_abc123",
            utterance="I live at 123 Main Street in Brooklyn, New York, zip 11201",
        )

        assert result["street"] == "123 Main Street"
        assert result["city"] == "Brooklyn"
        assert result["state"] == "NY"
        assert result["zip"] == "11201"

    @pytest.mark.asyncio
    async def test_extract_email_from_utterance(
        self, clinic_id, mock_llm_gateway, mock_graphiti
    ):
        """Extracts email address from speech including spelled-out forms."""
        from app.agents.intake import IntakeAgent

        agent = IntakeAgent(clinic_id=clinic_id)
        agent.llm = mock_llm_gateway
        agent.memory = mock_graphiti

        mock_llm_gateway.route.return_value = {
            "content": '{"email": "maria.santos@gmail.com"}',
            "model_used": "ollama/deepseek-coder-v2",
            "tokens_used": 16,
            "cost_usd": 0.0,
        }

        result = await agent.extract_email(
            call_id="call_abc123",
            utterance="My email is maria dot santos at gmail dot com",
        )

        assert result["email"] == "maria.santos@gmail.com"

    @pytest.mark.asyncio
    async def test_extract_demographics_uses_local_llm(
        self, clinic_id, mock_llm_gateway, mock_graphiti
    ):
        """All demographics extraction uses local model — never Claude."""
        from app.agents.intake import IntakeAgent

        agent = IntakeAgent(clinic_id=clinic_id)
        agent.llm = mock_llm_gateway
        agent.memory = mock_graphiti

        mock_llm_gateway.route.return_value = {
            "content": '{"date_of_birth": "1985-03-15"}',
            "model_used": "ollama/deepseek-coder-v2",
            "tokens_used": 14,
            "cost_usd": 0.0,
        }

        await agent.extract_date_of_birth(
            call_id="call_abc123",
            utterance="March 15, 1985",
        )

        call_kwargs = mock_llm_gateway.route.call_args[1]
        assert call_kwargs["task_type"] == "entity_extraction"


class TestIntakeAgentInsuranceCollection:
    """Insurance information collection."""

    @pytest.mark.asyncio
    async def test_extract_insurance_carrier_from_utterance(
        self, clinic_id, mock_llm_gateway, mock_graphiti
    ):
        """Extracts insurance carrier name from speech."""
        from app.agents.intake import IntakeAgent

        agent = IntakeAgent(clinic_id=clinic_id)
        agent.llm = mock_llm_gateway
        agent.memory = mock_graphiti

        mock_llm_gateway.route.return_value = {
            "content": '{"carrier": "BlueCross BlueShield", "plan_type": "PPO"}',
            "model_used": "ollama/deepseek-coder-v2",
            "tokens_used": 18,
            "cost_usd": 0.0,
        }

        result = await agent.extract_insurance_info(
            call_id="call_abc123",
            utterance="I have BlueCross BlueShield, it's a PPO plan",
        )

        assert result["carrier"] == "BlueCross BlueShield"
        assert result["plan_type"] == "PPO"

    @pytest.mark.asyncio
    async def test_extract_member_id_from_utterance(
        self, clinic_id, mock_llm_gateway, mock_graphiti
    ):
        """Extracts insurance member ID from speech."""
        from app.agents.intake import IntakeAgent

        agent = IntakeAgent(clinic_id=clinic_id)
        agent.llm = mock_llm_gateway
        agent.memory = mock_graphiti

        mock_llm_gateway.route.return_value = {
            "content": '{"member_id": "BCB123456789", "group_number": "GRP001"}',
            "model_used": "ollama/deepseek-coder-v2",
            "tokens_used": 22,
            "cost_usd": 0.0,
        }

        result = await agent.extract_member_id(
            call_id="call_abc123",
            utterance="My member ID is B C B 1 2 3 4 5 6 7 8 9 and group number GRP001",
        )

        assert result["member_id"] == "BCB123456789"

    @pytest.mark.asyncio
    async def test_missing_insurance_returns_uninsured_flag(
        self, clinic_id, mock_llm_gateway, mock_graphiti
    ):
        """
        When patient states they have no insurance,
        uninsured flag is set — not an error.
        """
        from app.agents.intake import IntakeAgent

        agent = IntakeAgent(clinic_id=clinic_id)
        agent.llm = mock_llm_gateway
        agent.memory = mock_graphiti

        mock_llm_gateway.route.return_value = {
            "content": '{"carrier": null, "uninsured": true}',
            "model_used": "ollama/deepseek-coder-v2",
            "tokens_used": 12,
            "cost_usd": 0.0,
        }

        result = await agent.extract_insurance_info(
            call_id="call_abc123",
            utterance="I don't have any insurance right now",
        )

        assert result.get("uninsured") is True


class TestIntakeAgentMedicalHistory:
    """Medical history and symptoms collection."""

    @pytest.mark.asyncio
    async def test_extract_current_medications(
        self, clinic_id, mock_llm_gateway, mock_graphiti
    ):
        """Extracts list of current medications from speech."""
        from app.agents.intake import IntakeAgent

        agent = IntakeAgent(clinic_id=clinic_id)
        agent.llm = mock_llm_gateway
        agent.memory = mock_graphiti

        mock_llm_gateway.route.return_value = {
            "content": (
                '{"medications": ['
                '{"name": "Lisinopril", "dose": "10mg", "frequency": "daily"}, '
                '{"name": "Metformin", "dose": "500mg", "frequency": "twice daily"}'
                ']}'
            ),
            "model_used": "ollama/deepseek-coder-v2",
            "tokens_used": 45,
            "cost_usd": 0.0,
        }

        result = await agent.extract_medications(
            call_id="call_abc123",
            utterance="I take Lisinopril 10mg daily and Metformin 500mg twice a day",
        )

        assert "medications" in result
        assert len(result["medications"]) == 2
        assert result["medications"][0]["name"] == "Lisinopril"

    @pytest.mark.asyncio
    async def test_extract_allergies_from_utterance(
        self, clinic_id, mock_llm_gateway, mock_graphiti
    ):
        """Extracts allergy list with reaction type."""
        from app.agents.intake import IntakeAgent

        agent = IntakeAgent(clinic_id=clinic_id)
        agent.llm = mock_llm_gateway
        agent.memory = mock_graphiti

        mock_llm_gateway.route.return_value = {
            "content": (
                '{"allergies": ['
                '{"substance": "Penicillin", "reaction": "hives"}, '
                '{"substance": "Sulfa drugs", "reaction": "rash"}'
                ']}'
            ),
            "model_used": "ollama/deepseek-coder-v2",
            "tokens_used": 38,
            "cost_usd": 0.0,
        }

        result = await agent.extract_allergies(
            call_id="call_abc123",
            utterance="I'm allergic to penicillin, I get hives, and sulfa drugs give me a rash",
        )

        assert "allergies" in result
        assert len(result["allergies"]) == 2
        assert result["allergies"][0]["substance"] == "Penicillin"

    @pytest.mark.asyncio
    async def test_extract_no_allergies_returns_nkda(
        self, clinic_id, mock_llm_gateway, mock_graphiti
    ):
        """
        'No known drug allergies' — returns NKDA flag.
        Standard medical terminology.
        """
        from app.agents.intake import IntakeAgent

        agent = IntakeAgent(clinic_id=clinic_id)
        agent.llm = mock_llm_gateway
        agent.memory = mock_graphiti

        mock_llm_gateway.route.return_value = {
            "content": '{"allergies": [], "nkda": true}',
            "model_used": "ollama/deepseek-coder-v2",
            "tokens_used": 12,
            "cost_usd": 0.0,
        }

        result = await agent.extract_allergies(
            call_id="call_abc123",
            utterance="No, I don't have any allergies",
        )

        assert result.get("nkda") is True

    @pytest.mark.asyncio
    async def test_extract_visit_reason_and_symptoms(
        self, clinic_id, mock_llm_gateway, mock_graphiti
    ):
        """Extracts visit reason and symptom details."""
        from app.agents.intake import IntakeAgent

        agent = IntakeAgent(clinic_id=clinic_id)
        agent.llm = mock_llm_gateway
        agent.memory = mock_graphiti

        mock_llm_gateway.route.return_value = {
            "content": (
                '{"reason": "chest pain", '
                '"symptoms": ["chest tightness", "shortness of breath"], '
                '"duration": "3 days", '
                '"severity": 6}'
            ),
            "model_used": "ollama/deepseek-coder-v2",
            "tokens_used": 35,
            "cost_usd": 0.0,
        }

        result = await agent.extract_visit_reason(
            call_id="call_abc123",
            utterance=(
                "I've had chest tightness and shortness of breath "
                "for about 3 days, maybe a 6 out of 10 pain"
            ),
        )

        assert result["reason"] == "chest pain"
        assert "shortness of breath" in result["symptoms"]
        assert result["duration"] == "3 days"

    @pytest.mark.asyncio
    async def test_medical_history_uses_local_llm(
        self, clinic_id, mock_llm_gateway, mock_graphiti
    ):
        """Medical history extraction uses local model — not Claude."""
        from app.agents.intake import IntakeAgent

        agent = IntakeAgent(clinic_id=clinic_id)
        agent.llm = mock_llm_gateway
        agent.memory = mock_graphiti

        mock_llm_gateway.route.return_value = {
            "content": '{"medications": []}',
            "model_used": "ollama/deepseek-coder-v2",
            "tokens_used": 8,
            "cost_usd": 0.0,
        }

        await agent.extract_medications(
            call_id="call_abc123",
            utterance="I don't take any medications",
        )

        call_kwargs = mock_llm_gateway.route.call_args[1]
        assert call_kwargs["task_type"] == "entity_extraction"


class TestIntakeAgentValidation:
    """Intake data validation and completeness."""

    def test_validate_complete_intake_passes(self, clinic_id):
        """Complete intake data passes validation."""
        from app.agents.intake import IntakeAgent

        agent = IntakeAgent(clinic_id=clinic_id)

        intake_data = {
            "first_name": "Maria",
            "last_name": "Santos",
            "date_of_birth": "1985-03-15",
            "phone": "+12125551234",
            "insurance": {"carrier": "BlueCross", "member_id": "BCB123"},
            "medications": [],
            "allergies": [],
            "visit_reason": "annual checkup",
        }

        result = agent.validate_intake(intake_data)
        assert result["valid"] is True
        assert len(result["missing_fields"]) == 0

    def test_validate_missing_required_fields_fails(self, clinic_id):
        """Missing required fields are reported."""
        from app.agents.intake import IntakeAgent

        agent = IntakeAgent(clinic_id=clinic_id)

        incomplete_data = {
            "first_name": "Maria",
            # missing last_name, date_of_birth, etc.
        }

        result = agent.validate_intake(incomplete_data)
        assert result["valid"] is False
        assert "last_name" in result["missing_fields"]
        assert "date_of_birth" in result["missing_fields"]

    def test_validate_returns_completion_percentage(self, clinic_id):
        """Validation returns how complete the intake is."""
        from app.agents.intake import IntakeAgent

        agent = IntakeAgent(clinic_id=clinic_id)

        partial_data = {
            "first_name": "Maria",
            "last_name": "Santos",
            "date_of_birth": "1985-03-15",
            "phone": "+12125551234",
        }

        result = agent.validate_intake(partial_data)
        assert "completion_pct" in result
        assert 0 < result["completion_pct"] < 100


class TestIntakeAgentEHRWriteback:
    """Patient data write-back to EHR."""

    @pytest.mark.asyncio
    async def test_submit_intake_to_ehr_calls_create_patient(
        self, clinic_id, mock_llm_gateway, mock_graphiti, mock_ehr_client
    ):
        """
        Submitting intake for a new patient calls EHR create_patient.
        Write-back is mandatory — intake is useless if not in EHR.
        """
        from app.agents.intake import IntakeAgent

        agent = IntakeAgent(clinic_id=clinic_id)
        agent.llm = mock_llm_gateway
        agent.memory = mock_graphiti
        agent.ehr = mock_ehr_client

        intake_data = {
            "first_name": "Maria",
            "last_name": "Santos",
            "date_of_birth": "1985-03-15",
            "phone": "+12125551234",
            "insurance": {"carrier": "BlueCross", "member_id": "BCB123"},
            "medications": [],
            "allergies": [],
            "visit_reason": "annual checkup",
        }

        result = await agent.submit_intake_to_ehr(
            call_id="call_abc123",
            patient_id=None,
            intake_data=intake_data,
        )

        assert result["success"] is True
        mock_ehr_client.create_patient.assert_called_once()

    @pytest.mark.asyncio
    async def test_submit_intake_existing_patient_updates_record(
        self, clinic_id, mock_llm_gateway, mock_graphiti, mock_ehr_client
    ):
        """Existing patient triggers update, not create."""
        from app.agents.intake import IntakeAgent

        agent = IntakeAgent(clinic_id=clinic_id)
        agent.llm = mock_llm_gateway
        agent.memory = mock_graphiti
        agent.ehr = mock_ehr_client

        mock_ehr_client.update_patient = AsyncMock(
            return_value={"patient_id": "PAT_001", "updated": True}
        )

        intake_data = {
            "medications": [{"name": "Lisinopril", "dose": "10mg"}],
            "allergies": [],
            "visit_reason": "follow-up",
        }

        result = await agent.submit_intake_to_ehr(
            call_id="call_abc123",
            patient_id="PAT_001",
            intake_data=intake_data,
        )

        assert result["success"] is True
        mock_ehr_client.update_patient.assert_called_once()

    @pytest.mark.asyncio
    async def test_submit_intake_ehr_failure_returns_error(
        self, clinic_id, mock_llm_gateway, mock_graphiti, mock_ehr_client
    ):
        """EHR write failure returns error — never crashes call."""
        from app.agents.intake import IntakeAgent

        agent = IntakeAgent(clinic_id=clinic_id)
        agent.llm = mock_llm_gateway
        agent.memory = mock_graphiti
        agent.ehr = mock_ehr_client

        mock_ehr_client.create_patient.side_effect = Exception("EHR timeout")

        result = await agent.submit_intake_to_ehr(
            call_id="call_abc123",
            patient_id=None,
            intake_data={"first_name": "Maria"},
        )

        assert result["success"] is False
        assert "error" in result


class TestIntakeAgentHIPAACompliance:
    """HIPAA requirements — PHI collection must be audit logged."""

    @pytest.mark.asyncio
    async def test_intake_submission_writes_audit_log(
        self, clinic_id, mock_llm_gateway, mock_graphiti, mock_ehr_client
    ):
        """
        Every intake submission writes to HIPAA audit log.
        PHI collection must always be traceable.
        """
        from app.agents.intake import IntakeAgent

        agent = IntakeAgent(clinic_id=clinic_id)
        agent.llm = mock_llm_gateway
        agent.memory = mock_graphiti
        agent.ehr = mock_ehr_client

        with patch("app.agents.intake.write_audit_log") as mock_audit:
            await agent.submit_intake_to_ehr(
                call_id="call_abc123",
                patient_id=None,
                intake_data={"first_name": "Maria", "last_name": "Santos"},
            )

            mock_audit.assert_called_once()
            kwargs = mock_audit.call_args[1]
            assert kwargs["event_type"] == "intake_submitted"
            assert kwargs["clinic_id"] == clinic_id

    @pytest.mark.asyncio
    async def test_intake_stores_graphiti_episode(
        self, clinic_id, mock_llm_gateway, mock_graphiti, mock_ehr_client
    ):
        """Completed intake stored in Graphiti for future agent context."""
        from app.agents.intake import IntakeAgent

        agent = IntakeAgent(clinic_id=clinic_id)
        agent.llm = mock_llm_gateway
        agent.memory = mock_graphiti
        agent.ehr = mock_ehr_client

        await agent.submit_intake_to_ehr(
            call_id="call_abc123",
            patient_id="PAT_001",
            intake_data={"visit_reason": "annual checkup"},
        )

        mock_graphiti.add_episode.assert_called_once()
        kwargs = mock_graphiti.add_episode.call_args[1]
        assert kwargs["clinic_id"] == clinic_id

    @pytest.mark.asyncio
    async def test_generate_provider_summary_uses_local_llm(
        self, clinic_id, mock_llm_gateway, mock_graphiti
    ):
        """
        Provider intake summary uses local LLM.
        Summarization is routine — never needs Claude.
        """
        from app.agents.intake import IntakeAgent

        agent = IntakeAgent(clinic_id=clinic_id)
        agent.llm = mock_llm_gateway
        agent.memory = mock_graphiti

        mock_llm_gateway.route.return_value = {
            "content": (
                "Patient: Maria Santos, DOB 03/15/1985. "
                "Presenting with chest tightness x3 days. "
                "Medications: Lisinopril 10mg daily. NKDA."
            ),
            "model_used": "ollama/qwen2.5:14b",
            "tokens_used": 42,
            "cost_usd": 0.0,
        }

        intake_data = {
            "first_name": "Maria",
            "last_name": "Santos",
            "date_of_birth": "1985-03-15",
            "medications": [{"name": "Lisinopril", "dose": "10mg"}],
            "allergies": [],
            "visit_reason": "chest tightness",
        }

        summary = await agent.generate_provider_summary(
            call_id="call_abc123",
            intake_data=intake_data,
        )

        assert summary is not None
        assert len(summary) > 0
        call_kwargs = mock_llm_gateway.route.call_args[1]
        assert call_kwargs["task_type"] == "patient_intake_summarize"
