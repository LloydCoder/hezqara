"""
Reception Agent Tests — Sprint 1
TDD RED phase: all tests written before implementation exists.

The Reception Agent handles every inbound patient call via Retell AI.
It is the first touchpoint between a patient and the clinic.

Responsibilities:
  - Greet caller warmly, identify the clinic
  - Determine call intent (appointment, refill, records, general)
  - Collect patient information
  - Route to appropriate specialist agent
  - Handle transfers to human staff when needed
  - Log every interaction for HIPAA audit trail
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# ── Import paths — these don't exist yet (RED phase) ─────────────────────────
# These imports WILL fail until implementation is built.
# That is the correct TDD state.

class TestReceptionAgentInitialisation:
    """Agent must initialise correctly with clinic context."""

    def test_reception_agent_can_be_imported(self):
        """Import must succeed once implementation exists."""
        from app.agents.reception import ReceptionAgent
        assert ReceptionAgent is not None

    def test_reception_agent_inherits_base_agent(self):
        """Reception agent must extend BaseAgent."""
        from app.agents.reception import ReceptionAgent
        from app.agents.base_agent import BaseAgent
        assert issubclass(ReceptionAgent, BaseAgent)

    def test_reception_agent_requires_clinic_id(self):
        """Cannot instantiate without a clinic_id."""
        from app.agents.reception import ReceptionAgent
        with pytest.raises(TypeError):
            ReceptionAgent()

    def test_reception_agent_stores_clinic_id(self, clinic_id):
        """clinic_id is stored on the instance."""
        from app.agents.reception import ReceptionAgent
        agent = ReceptionAgent(clinic_id=clinic_id)
        assert agent.clinic_id == clinic_id

    def test_reception_agent_has_agent_type(self, clinic_id):
        """Agent type is 'reception'."""
        from app.agents.reception import ReceptionAgent
        agent = ReceptionAgent(clinic_id=clinic_id)
        assert agent.agent_type == "reception"


class TestReceptionAgentCallHandling:
    """Core call handling behaviour."""

    @pytest.mark.asyncio
    async def test_handle_call_started_returns_greeting(
        self, clinic_id, clinic_context, mock_llm_gateway, mock_graphiti
    ):
        """
        When a call starts, agent generates a warm greeting
        that includes the clinic name.
        """
        from app.agents.reception import ReceptionAgent

        agent = ReceptionAgent(clinic_id=clinic_id)
        agent.llm = mock_llm_gateway
        agent.memory = mock_graphiti

        mock_graphiti.get_clinic_context.return_value = clinic_context
        mock_llm_gateway.route.return_value = {
            "content": "Thank you for calling Family Care Associates. How can I help you today?",
            "model_used": "ollama/qwen2.5:14b",
            "tokens_used": 28,
            "cost_usd": 0.0,
        }

        result = await agent.handle_call_started(
            call_id="call_abc123",
            from_number="+12125551234",
        )

        assert result["greeting"] is not None
        assert len(result["greeting"]) > 0
        assert result["call_id"] == "call_abc123"
        mock_graphiti.get_clinic_context.assert_called_once_with(clinic_id)

    @pytest.mark.asyncio
    async def test_handle_call_started_uses_local_llm(
        self, clinic_id, clinic_context, mock_llm_gateway, mock_graphiti
    ):
        """
        Greeting generation uses local LLM (Ollama) not Claude.
        Cost must be $0.00 for greeting.
        """
        from app.agents.reception import ReceptionAgent

        agent = ReceptionAgent(clinic_id=clinic_id)
        agent.llm = mock_llm_gateway
        agent.memory = mock_graphiti

        mock_graphiti.get_clinic_context.return_value = clinic_context

        result = await agent.handle_call_started(
            call_id="call_abc123",
            from_number="+12125551234",
        )

        call_args = mock_llm_gateway.route.call_args
        assert call_args[1]["task_type"] == "reception_greeting"

    @pytest.mark.asyncio
    async def test_detect_intent_appointment(
        self, clinic_id, mock_llm_gateway, mock_graphiti
    ):
        """
        When patient says they want to book an appointment,
        intent is 'appointment'.
        """
        from app.agents.reception import ReceptionAgent

        agent = ReceptionAgent(clinic_id=clinic_id)
        agent.llm = mock_llm_gateway
        agent.memory = mock_graphiti

        mock_llm_gateway.route.return_value = {
            "content": '{"intent": "appointment", "confidence": 0.97}',
            "model_used": "ollama/deepseek-coder-v2",
            "tokens_used": 15,
            "cost_usd": 0.0,
        }

        intent = await agent.detect_intent(
            call_id="call_abc123",
            utterance="I need to schedule an appointment with Dr. Chen",
        )

        assert intent["intent"] == "appointment"
        assert intent["confidence"] >= 0.8

    @pytest.mark.asyncio
    async def test_detect_intent_refill(
        self, clinic_id, mock_llm_gateway, mock_graphiti
    ):
        """Refill request is correctly classified."""
        from app.agents.reception import ReceptionAgent

        agent = ReceptionAgent(clinic_id=clinic_id)
        agent.llm = mock_llm_gateway
        agent.memory = mock_graphiti

        mock_llm_gateway.route.return_value = {
            "content": '{"intent": "refill", "confidence": 0.95}',
            "model_used": "ollama/deepseek-coder-v2",
            "tokens_used": 12,
            "cost_usd": 0.0,
        }

        intent = await agent.detect_intent(
            call_id="call_abc123",
            utterance="I'm running out of my blood pressure medication",
        )

        assert intent["intent"] == "refill"

    @pytest.mark.asyncio
    async def test_detect_intent_general_inquiry(
        self, clinic_id, mock_llm_gateway, mock_graphiti
    ):
        """General inquiry is classified correctly."""
        from app.agents.reception import ReceptionAgent

        agent = ReceptionAgent(clinic_id=clinic_id)
        agent.llm = mock_llm_gateway
        agent.memory = mock_graphiti

        mock_llm_gateway.route.return_value = {
            "content": '{"intent": "general", "confidence": 0.88}',
            "model_used": "ollama/deepseek-coder-v2",
            "tokens_used": 10,
            "cost_usd": 0.0,
        }

        intent = await agent.detect_intent(
            call_id="call_abc123",
            utterance="What are your office hours?",
        )

        assert intent["intent"] == "general"

    @pytest.mark.asyncio
    async def test_detect_intent_emergency_triggers_human_transfer(
        self, clinic_id, mock_llm_gateway, mock_graphiti
    ):
        """
        If caller indicates emergency, intent is 'emergency'
        and transfer_to_human flag is True.
        PATIENT SAFETY — this must never fail.
        """
        from app.agents.reception import ReceptionAgent

        agent = ReceptionAgent(clinic_id=clinic_id)
        agent.llm = mock_llm_gateway
        agent.memory = mock_graphiti

        mock_llm_gateway.route.return_value = {
            "content": '{"intent": "emergency", "confidence": 0.99}',
            "model_used": "ollama/deepseek-coder-v2",
            "tokens_used": 8,
            "cost_usd": 0.0,
        }

        intent = await agent.detect_intent(
            call_id="call_abc123",
            utterance="I'm having severe chest pains",
        )

        assert intent["intent"] == "emergency"
        assert intent["transfer_to_human"] is True


class TestReceptionAgentPatientIdentification:
    """Patient identification and verification."""

    @pytest.mark.asyncio
    async def test_identify_patient_by_phone_number(
        self, clinic_id, mock_llm_gateway, mock_graphiti, mock_ehr_client, patient_data
    ):
        """
        Known patient calling from registered number
        is identified without asking for details.
        """
        from app.agents.reception import ReceptionAgent

        agent = ReceptionAgent(clinic_id=clinic_id)
        agent.llm = mock_llm_gateway
        agent.memory = mock_graphiti
        agent.ehr = mock_ehr_client

        mock_ehr_client.get_patient.return_value = {
            "patient_id": "PAT_001",
            **patient_data,
        }

        result = await agent.identify_patient(
            call_id="call_abc123",
            from_number="+12125551234",
        )

        assert result["identified"] is True
        assert result["patient_id"] == "PAT_001"
        assert result["requires_verification"] is False

    @pytest.mark.asyncio
    async def test_unknown_patient_requires_name_collection(
        self, clinic_id, mock_llm_gateway, mock_graphiti, mock_ehr_client
    ):
        """
        Unknown phone number — agent must collect patient name.
        """
        from app.agents.reception import ReceptionAgent

        agent = ReceptionAgent(clinic_id=clinic_id)
        agent.llm = mock_llm_gateway
        agent.memory = mock_graphiti
        agent.ehr = mock_ehr_client

        mock_ehr_client.get_patient.return_value = None

        result = await agent.identify_patient(
            call_id="call_abc123",
            from_number="+19995550000",
        )

        assert result["identified"] is False
        assert result["requires_name"] is True

    @pytest.mark.asyncio
    async def test_collect_patient_name_extracts_first_last(
        self, clinic_id, mock_llm_gateway, mock_graphiti
    ):
        """
        From natural speech, extract first and last name correctly.
        """
        from app.agents.reception import ReceptionAgent

        agent = ReceptionAgent(clinic_id=clinic_id)
        agent.llm = mock_llm_gateway
        agent.memory = mock_graphiti

        mock_llm_gateway.route.return_value = {
            "content": '{"first_name": "Maria", "last_name": "Santos"}',
            "model_used": "ollama/deepseek-coder-v2",
            "tokens_used": 18,
            "cost_usd": 0.0,
        }

        name = await agent.extract_patient_name(
            call_id="call_abc123",
            utterance="My name is Maria Santos",
        )

        assert name["first_name"] == "Maria"
        assert name["last_name"] == "Santos"


class TestReceptionAgentRouting:
    """Agent routing — handoff to specialist agents."""

    @pytest.mark.asyncio
    async def test_appointment_intent_routes_to_scheduling_agent(
        self, clinic_id, mock_llm_gateway, mock_graphiti
    ):
        """
        After appointment intent is confirmed,
        agent signals handoff to Scheduling Agent.
        """
        from app.agents.reception import ReceptionAgent

        agent = ReceptionAgent(clinic_id=clinic_id)
        agent.llm = mock_llm_gateway
        agent.memory = mock_graphiti

        result = await agent.route_to_specialist(
            call_id="call_abc123",
            intent="appointment",
            patient_id="PAT_001",
        )

        assert result["next_agent"] == "scheduling"
        assert result["call_id"] == "call_abc123"
        assert result["patient_id"] == "PAT_001"

    @pytest.mark.asyncio
    async def test_refill_intent_routes_to_refill_agent(
        self, clinic_id, mock_llm_gateway, mock_graphiti
    ):
        """Refill intent routes to Refill Agent."""
        from app.agents.reception import ReceptionAgent

        agent = ReceptionAgent(clinic_id=clinic_id)
        agent.llm = mock_llm_gateway
        agent.memory = mock_graphiti

        result = await agent.route_to_specialist(
            call_id="call_abc123",
            intent="refill",
            patient_id="PAT_001",
        )

        assert result["next_agent"] == "refill"

    @pytest.mark.asyncio
    async def test_insurance_intent_routes_to_insurance_agent(
        self, clinic_id, mock_llm_gateway, mock_graphiti
    ):
        """Insurance question routes to Insurance Agent."""
        from app.agents.reception import ReceptionAgent

        agent = ReceptionAgent(clinic_id=clinic_id)
        agent.llm = mock_llm_gateway
        agent.memory = mock_graphiti

        result = await agent.route_to_specialist(
            call_id="call_abc123",
            intent="insurance",
            patient_id="PAT_001",
        )

        assert result["next_agent"] == "insurance"

    @pytest.mark.asyncio
    async def test_unknown_intent_stays_with_reception(
        self, clinic_id, mock_llm_gateway, mock_graphiti
    ):
        """Unknown intent stays with reception — no blind routing."""
        from app.agents.reception import ReceptionAgent

        agent = ReceptionAgent(clinic_id=clinic_id)
        agent.llm = mock_llm_gateway
        agent.memory = mock_graphiti

        result = await agent.route_to_specialist(
            call_id="call_abc123",
            intent="unknown",
            patient_id="PAT_001",
        )

        assert result["next_agent"] == "reception"


class TestReceptionAgentHIPAACompliance:
    """
    HIPAA compliance is non-negotiable.
    These tests must pass before any production deployment.
    """

    @pytest.mark.asyncio
    async def test_call_start_writes_audit_log(
        self, clinic_id, clinic_context, mock_llm_gateway, mock_graphiti
    ):
        """
        Every call start is written to HIPAA audit log.
        PHI access must be traceable.
        """
        from app.agents.reception import ReceptionAgent

        agent = ReceptionAgent(clinic_id=clinic_id)
        agent.llm = mock_llm_gateway
        agent.memory = mock_graphiti
        mock_graphiti.get_clinic_context.return_value = clinic_context

        with patch("app.agents.reception.write_audit_log") as mock_audit:
            await agent.handle_call_started(
                call_id="call_abc123",
                from_number="+12125551234",
            )
            mock_audit.assert_called_once()
            audit_args = mock_audit.call_args[1]
            assert audit_args["event_type"] == "call_started"
            assert audit_args["call_id"] == "call_abc123"

    @pytest.mark.asyncio
    async def test_call_end_writes_audit_log(
        self, clinic_id, mock_llm_gateway, mock_graphiti, retell_call_ended_payload
    ):
        """Call end is also logged with duration."""
        from app.agents.reception import ReceptionAgent

        agent = ReceptionAgent(clinic_id=clinic_id)
        agent.llm = mock_llm_gateway
        agent.memory = mock_graphiti

        with patch("app.agents.reception.write_audit_log") as mock_audit:
            await agent.handle_call_ended(
                call_data=retell_call_ended_payload["call"]
            )
            mock_audit.assert_called_once()
            audit_args = mock_audit.call_args[1]
            assert audit_args["event_type"] == "call_ended"

    def test_phone_number_is_never_logged_in_plain_text(self, clinic_id):
        """
        Raw phone numbers must not appear in logs.
        They must be masked: +1212555**** format.
        """
        from app.agents.reception import ReceptionAgent
        from app.utils.phone_formatter import mask_phone_number

        masked = mask_phone_number("+12125551234")
        assert "1234" not in masked
        assert "*" in masked

    @pytest.mark.asyncio
    async def test_agent_stores_episode_in_graphiti_after_call(
        self, clinic_id, mock_llm_gateway, mock_graphiti, retell_call_ended_payload
    ):
        """
        After every call, a Graphiti episode is stored.
        This builds the persistent memory graph.
        """
        from app.agents.reception import ReceptionAgent

        agent = ReceptionAgent(clinic_id=clinic_id)
        agent.llm = mock_llm_gateway
        agent.memory = mock_graphiti

        await agent.handle_call_ended(
            call_data=retell_call_ended_payload["call"]
        )

        mock_graphiti.add_episode.assert_called_once()
        episode_args = mock_graphiti.add_episode.call_args[1]
        assert episode_args["clinic_id"] == clinic_id
        assert "call_id" in episode_args


class TestReceptionAgentCostControl:
    """
    Token cost control — 80% of reception tasks must use
    local Ollama models at $0 cost.
    """

    @pytest.mark.asyncio
    async def test_greeting_task_type_is_local(
        self, clinic_id, clinic_context, mock_llm_gateway, mock_graphiti
    ):
        """Greeting uses local model — task_type routes to Ollama."""
        from app.agents.reception import ReceptionAgent

        agent = ReceptionAgent(clinic_id=clinic_id)
        agent.llm = mock_llm_gateway
        agent.memory = mock_graphiti
        mock_graphiti.get_clinic_context.return_value = clinic_context

        await agent.handle_call_started(
            call_id="call_abc123",
            from_number="+12125551234",
        )

        call_args = mock_llm_gateway.route.call_args[1]
        assert call_args["task_type"] in [
            "reception_greeting",
            "intent_detection",
            "entity_extraction",
        ]

    @pytest.mark.asyncio
    async def test_intent_detection_uses_local_model(
        self, clinic_id, mock_llm_gateway, mock_graphiti
    ):
        """Intent detection must never call Claude directly."""
        from app.agents.reception import ReceptionAgent

        agent = ReceptionAgent(clinic_id=clinic_id)
        agent.llm = mock_llm_gateway
        agent.memory = mock_graphiti

        mock_llm_gateway.route.return_value = {
            "content": '{"intent": "appointment", "confidence": 0.95}',
            "model_used": "ollama/deepseek-coder-v2",
            "tokens_used": 14,
            "cost_usd": 0.0,
        }

        await agent.detect_intent(
            call_id="call_abc123",
            utterance="I need to make an appointment",
        )

        call_args = mock_llm_gateway.route.call_args[1]
        assert call_args["task_type"] == "intent_detection"
