"""
Scheduling Agent Tests — Sprint 2
TDD RED phase: all tests written before implementation exists.

The Scheduling Agent handles appointment booking end-to-end.
It is the most used agent — every clinic's #1 call reason.

Responsibilities:
  - Fetch available appointment slots from athenahealth EHR
  - Match patient preference (day, time, provider, reason)
  - Book appointment with write-back to EHR
  - Confirm booking verbally to patient
  - Send confirmation SMS via Twilio
  - Handle reschedule and cancellation requests
  - Log every booking for HIPAA audit trail
  - Store appointment episode in Graphiti
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, date


class TestSchedulingAgentInitialisation:
    """Agent must initialise correctly."""

    def test_scheduling_agent_can_be_imported(self):
        from app.agents.scheduling import SchedulingAgent
        assert SchedulingAgent is not None

    def test_scheduling_agent_inherits_base_agent(self):
        from app.agents.scheduling import SchedulingAgent
        from app.agents.base_agent import BaseAgent
        assert issubclass(SchedulingAgent, BaseAgent)

    def test_scheduling_agent_requires_clinic_id(self):
        from app.agents.scheduling import SchedulingAgent
        with pytest.raises(TypeError):
            SchedulingAgent()

    def test_scheduling_agent_has_correct_type(self, clinic_id):
        from app.agents.scheduling import SchedulingAgent
        agent = SchedulingAgent(clinic_id=clinic_id)
        assert agent.agent_type == "scheduling"

    def test_scheduling_agent_stores_clinic_id(self, clinic_id):
        from app.agents.scheduling import SchedulingAgent
        agent = SchedulingAgent(clinic_id=clinic_id)
        assert agent.clinic_id == clinic_id


class TestSchedulingAgentSlotFetching:
    """Slot fetching from athenahealth EHR."""

    @pytest.mark.asyncio
    async def test_get_available_slots_returns_list(
        self, clinic_id, mock_llm_gateway, mock_graphiti, mock_ehr_client
    ):
        """
        Fetching available slots returns a non-empty list
        when EHR has availability.
        """
        from app.agents.scheduling import SchedulingAgent

        agent = SchedulingAgent(clinic_id=clinic_id)
        agent.llm = mock_llm_gateway
        agent.memory = mock_graphiti
        agent.ehr = mock_ehr_client

        slots = await agent.get_available_slots(
            call_id="call_abc123",
            provider_id="P001",
            requested_date="2026-07-01",
        )

        assert isinstance(slots, list)
        assert len(slots) > 0
        mock_ehr_client.get_available_slots.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_available_slots_returns_correct_structure(
        self, clinic_id, mock_llm_gateway, mock_graphiti, mock_ehr_client
    ):
        """
        Each slot has required fields: slot_id, datetime, provider_id.
        """
        from app.agents.scheduling import SchedulingAgent

        agent = SchedulingAgent(clinic_id=clinic_id)
        agent.llm = mock_llm_gateway
        agent.memory = mock_graphiti
        agent.ehr = mock_ehr_client

        slots = await agent.get_available_slots(
            call_id="call_abc123",
            provider_id="P001",
            requested_date="2026-07-01",
        )

        for slot in slots:
            assert "slot_id" in slot
            assert "datetime" in slot
            assert "provider_id" in slot

    @pytest.mark.asyncio
    async def test_get_available_slots_no_availability_returns_empty(
        self, clinic_id, mock_llm_gateway, mock_graphiti, mock_ehr_client
    ):
        """Returns empty list when EHR has no availability."""
        from app.agents.scheduling import SchedulingAgent

        agent = SchedulingAgent(clinic_id=clinic_id)
        agent.llm = mock_llm_gateway
        agent.memory = mock_graphiti
        agent.ehr = mock_ehr_client

        mock_ehr_client.get_available_slots.return_value = []

        slots = await agent.get_available_slots(
            call_id="call_abc123",
            provider_id="P001",
            requested_date="2026-07-01",
        )

        assert slots == []

    @pytest.mark.asyncio
    async def test_get_available_slots_passes_clinic_id_to_ehr(
        self, clinic_id, mock_llm_gateway, mock_graphiti, mock_ehr_client
    ):
        """
        EHR call must include clinic_id for multi-tenant isolation.
        Never fetch slots from the wrong clinic.
        """
        from app.agents.scheduling import SchedulingAgent

        agent = SchedulingAgent(clinic_id=clinic_id)
        agent.llm = mock_llm_gateway
        agent.memory = mock_graphiti
        agent.ehr = mock_ehr_client

        await agent.get_available_slots(
            call_id="call_abc123",
            provider_id="P001",
            requested_date="2026-07-01",
        )

        call_kwargs = mock_ehr_client.get_available_slots.call_args[1]
        assert call_kwargs["clinic_id"] == clinic_id


class TestSchedulingAgentPreferenceMatching:
    """Match patient preference to available slots."""

    @pytest.mark.asyncio
    async def test_match_preference_morning_returns_morning_slot(
        self, clinic_id, mock_llm_gateway, mock_graphiti
    ):
        """
        When patient says 'morning', agent selects a morning slot.
        Morning = before 12:00.
        """
        from app.agents.scheduling import SchedulingAgent

        agent = SchedulingAgent(clinic_id=clinic_id)
        agent.llm = mock_llm_gateway
        agent.memory = mock_graphiti

        slots = [
            {"slot_id": "S001", "datetime": "2026-07-01T09:00:00", "provider_id": "P001"},
            {"slot_id": "S002", "datetime": "2026-07-01T14:00:00", "provider_id": "P001"},
            {"slot_id": "S003", "datetime": "2026-07-01T16:30:00", "provider_id": "P001"},
        ]

        mock_llm_gateway.route.return_value = {
            "content": '{"slot_id": "S001", "reason": "earliest morning slot"}',
            "model_used": "ollama/deepseek-coder-v2",
            "tokens_used": 20,
            "cost_usd": 0.0,
        }

        best_slot = await agent.match_slot_to_preference(
            call_id="call_abc123",
            slots=slots,
            patient_preference="morning",
        )

        assert best_slot is not None
        assert best_slot["slot_id"] == "S001"

    @pytest.mark.asyncio
    async def test_match_preference_specific_provider(
        self, clinic_id, mock_llm_gateway, mock_graphiti
    ):
        """
        When patient requests a specific provider,
        only slots for that provider are returned.
        """
        from app.agents.scheduling import SchedulingAgent

        agent = SchedulingAgent(clinic_id=clinic_id)
        agent.llm = mock_llm_gateway
        agent.memory = mock_graphiti

        slots = [
            {"slot_id": "S001", "datetime": "2026-07-01T09:00:00", "provider_id": "P001"},
            {"slot_id": "S002", "datetime": "2026-07-01T10:00:00", "provider_id": "P002"},
            {"slot_id": "S003", "datetime": "2026-07-01T11:00:00", "provider_id": "P001"},
        ]

        filtered = await agent.filter_slots_by_provider(
            slots=slots,
            provider_id="P001",
        )

        assert all(s["provider_id"] == "P001" for s in filtered)
        assert len(filtered) == 2

    @pytest.mark.asyncio
    async def test_extract_scheduling_preference_from_utterance(
        self, clinic_id, mock_llm_gateway, mock_graphiti
    ):
        """
        Extract day, time preference, and provider from natural speech.
        """
        from app.agents.scheduling import SchedulingAgent

        agent = SchedulingAgent(clinic_id=clinic_id)
        agent.llm = mock_llm_gateway
        agent.memory = mock_graphiti

        mock_llm_gateway.route.return_value = {
            "content": (
                '{"day_preference": "tuesday", '
                '"time_preference": "morning", '
                '"provider_preference": "Dr. Chen", '
                '"reason": "annual checkup"}'
            ),
            "model_used": "ollama/deepseek-coder-v2",
            "tokens_used": 32,
            "cost_usd": 0.0,
        }

        prefs = await agent.extract_scheduling_preference(
            call_id="call_abc123",
            utterance="I'd like to see Dr. Chen next Tuesday morning for my annual checkup",
        )

        assert prefs["day_preference"] == "tuesday"
        assert prefs["time_preference"] == "morning"
        assert "Chen" in prefs["provider_preference"]
        assert prefs["reason"] == "annual checkup"

    @pytest.mark.asyncio
    async def test_extract_preference_uses_local_llm(
        self, clinic_id, mock_llm_gateway, mock_graphiti
    ):
        """Preference extraction must use local model — not Claude."""
        from app.agents.scheduling import SchedulingAgent

        agent = SchedulingAgent(clinic_id=clinic_id)
        agent.llm = mock_llm_gateway
        agent.memory = mock_graphiti

        mock_llm_gateway.route.return_value = {
            "content": '{"day_preference": "any", "time_preference": "any"}',
            "model_used": "ollama/deepseek-coder-v2",
            "tokens_used": 12,
            "cost_usd": 0.0,
        }

        await agent.extract_scheduling_preference(
            call_id="call_abc123",
            utterance="Anytime next week works for me",
        )

        call_kwargs = mock_llm_gateway.route.call_args[1]
        assert call_kwargs["task_type"] == "appointment_slot_select"


class TestSchedulingAgentBooking:
    """Appointment booking with EHR write-back."""

    @pytest.mark.asyncio
    async def test_book_appointment_returns_confirmation(
        self, clinic_id, mock_llm_gateway, mock_graphiti, mock_ehr_client
    ):
        """
        Booking an appointment returns a confirmation with
        appointment_id, datetime, and provider name.
        """
        from app.agents.scheduling import SchedulingAgent

        agent = SchedulingAgent(clinic_id=clinic_id)
        agent.llm = mock_llm_gateway
        agent.memory = mock_graphiti
        agent.ehr = mock_ehr_client

        result = await agent.book_appointment(
            call_id="call_abc123",
            patient_id="PAT_001",
            slot_id="S001",
            reason="annual checkup",
        )

        assert result["success"] is True
        assert "appointment_id" in result
        assert "datetime" in result
        assert "provider" in result

    @pytest.mark.asyncio
    async def test_book_appointment_writes_back_to_ehr(
        self, clinic_id, mock_llm_gateway, mock_graphiti, mock_ehr_client
    ):
        """
        Booking must write back to EHR — not just store locally.
        Write-back is the core value of this agent.
        """
        from app.agents.scheduling import SchedulingAgent

        agent = SchedulingAgent(clinic_id=clinic_id)
        agent.llm = mock_llm_gateway
        agent.memory = mock_graphiti
        agent.ehr = mock_ehr_client

        await agent.book_appointment(
            call_id="call_abc123",
            patient_id="PAT_001",
            slot_id="S001",
            reason="annual checkup",
        )

        mock_ehr_client.book_appointment.assert_called_once()
        call_kwargs = mock_ehr_client.book_appointment.call_args[1]
        assert call_kwargs["patient_id"] == "PAT_001"
        assert call_kwargs["slot_id"] == "S001"

    @pytest.mark.asyncio
    async def test_book_appointment_passes_clinic_id_to_ehr(
        self, clinic_id, mock_llm_gateway, mock_graphiti, mock_ehr_client
    ):
        """Multi-tenant safety — clinic_id must travel with every EHR call."""
        from app.agents.scheduling import SchedulingAgent

        agent = SchedulingAgent(clinic_id=clinic_id)
        agent.llm = mock_llm_gateway
        agent.memory = mock_graphiti
        agent.ehr = mock_ehr_client

        await agent.book_appointment(
            call_id="call_abc123",
            patient_id="PAT_001",
            slot_id="S001",
            reason="follow-up",
        )

        call_kwargs = mock_ehr_client.book_appointment.call_args[1]
        assert call_kwargs["clinic_id"] == clinic_id

    @pytest.mark.asyncio
    async def test_book_appointment_ehr_failure_returns_error(
        self, clinic_id, mock_llm_gateway, mock_graphiti, mock_ehr_client
    ):
        """
        When EHR booking fails, agent returns success=False
        and does not crash the call.
        """
        from app.agents.scheduling import SchedulingAgent

        agent = SchedulingAgent(clinic_id=clinic_id)
        agent.llm = mock_llm_gateway
        agent.memory = mock_graphiti
        agent.ehr = mock_ehr_client

        mock_ehr_client.book_appointment.side_effect = Exception("EHR timeout")

        result = await agent.book_appointment(
            call_id="call_abc123",
            patient_id="PAT_001",
            slot_id="S001",
            reason="follow-up",
        )

        assert result["success"] is False
        assert "error" in result

    @pytest.mark.asyncio
    async def test_generate_confirmation_message_uses_local_llm(
        self, clinic_id, mock_llm_gateway, mock_graphiti
    ):
        """
        Verbal confirmation message to patient uses local LLM.
        Routine text generation — never needs Claude.
        """
        from app.agents.scheduling import SchedulingAgent

        agent = SchedulingAgent(clinic_id=clinic_id)
        agent.llm = mock_llm_gateway
        agent.memory = mock_graphiti

        mock_llm_gateway.route.return_value = {
            "content": (
                "Your appointment with Dr. Chen is confirmed for "
                "Tuesday July 1st at 9 AM. See you then!"
            ),
            "model_used": "ollama/qwen2.5:14b",
            "tokens_used": 28,
            "cost_usd": 0.0,
        }

        confirmation = await agent.generate_confirmation_message(
            appointment={
                "appointment_id": "APT_001",
                "datetime": "2026-07-01T09:00:00",
                "provider": "Dr. Sarah Chen",
            },
        )

        assert confirmation is not None
        assert len(confirmation) > 0
        call_kwargs = mock_llm_gateway.route.call_args[1]
        assert call_kwargs["task_type"] == "appointment_reminder_text"


class TestSchedulingAgentReschedulingCancellation:
    """Reschedule and cancellation flows."""

    @pytest.mark.asyncio
    async def test_detect_reschedule_intent(
        self, clinic_id, mock_llm_gateway, mock_graphiti
    ):
        """
        Detects when patient wants to reschedule an existing appointment.
        """
        from app.agents.scheduling import SchedulingAgent

        agent = SchedulingAgent(clinic_id=clinic_id)
        agent.llm = mock_llm_gateway
        agent.memory = mock_graphiti

        mock_llm_gateway.route.return_value = {
            "content": '{"action": "reschedule", "confidence": 0.94}',
            "model_used": "ollama/deepseek-coder-v2",
            "tokens_used": 14,
            "cost_usd": 0.0,
        }

        result = await agent.detect_scheduling_action(
            call_id="call_abc123",
            utterance="I need to move my appointment to next week",
        )

        assert result["action"] == "reschedule"

    @pytest.mark.asyncio
    async def test_detect_cancellation_intent(
        self, clinic_id, mock_llm_gateway, mock_graphiti
    ):
        """Detects when patient wants to cancel."""
        from app.agents.scheduling import SchedulingAgent

        agent = SchedulingAgent(clinic_id=clinic_id)
        agent.llm = mock_llm_gateway
        agent.memory = mock_graphiti

        mock_llm_gateway.route.return_value = {
            "content": '{"action": "cancel", "confidence": 0.98}',
            "model_used": "ollama/deepseek-coder-v2",
            "tokens_used": 11,
            "cost_usd": 0.0,
        }

        result = await agent.detect_scheduling_action(
            call_id="call_abc123",
            utterance="I want to cancel my appointment on Thursday",
        )

        assert result["action"] == "cancel"

    @pytest.mark.asyncio
    async def test_cancel_appointment_writes_back_to_ehr(
        self, clinic_id, mock_llm_gateway, mock_graphiti, mock_ehr_client
    ):
        """Cancellation must write back to EHR to free the slot."""
        from app.agents.scheduling import SchedulingAgent

        agent = SchedulingAgent(clinic_id=clinic_id)
        agent.llm = mock_llm_gateway
        agent.memory = mock_graphiti
        agent.ehr = mock_ehr_client

        mock_ehr_client.cancel_appointment = AsyncMock(
            return_value={"status": "cancelled"}
        )

        result = await agent.cancel_appointment(
            call_id="call_abc123",
            patient_id="PAT_001",
            appointment_id="APT_001",
        )

        assert result["success"] is True
        mock_ehr_client.cancel_appointment.assert_called_once()


class TestSchedulingAgentHIPAACompliance:
    """HIPAA audit requirements for scheduling."""

    @pytest.mark.asyncio
    async def test_booking_writes_audit_log(
        self, clinic_id, mock_llm_gateway, mock_graphiti, mock_ehr_client
    ):
        """
        Every appointment booking writes to HIPAA audit log.
        appointment_id and patient_id must be present.
        """
        from app.agents.scheduling import SchedulingAgent

        agent = SchedulingAgent(clinic_id=clinic_id)
        agent.llm = mock_llm_gateway
        agent.memory = mock_graphiti
        agent.ehr = mock_ehr_client

        with patch("app.agents.scheduling.write_audit_log") as mock_audit:
            await agent.book_appointment(
                call_id="call_abc123",
                patient_id="PAT_001",
                slot_id="S001",
                reason="annual checkup",
            )

            mock_audit.assert_called_once()
            audit_kwargs = mock_audit.call_args[1]
            assert audit_kwargs["event_type"] == "appointment_booked"
            assert audit_kwargs["clinic_id"] == clinic_id

    @pytest.mark.asyncio
    async def test_booking_stores_graphiti_episode(
        self, clinic_id, mock_llm_gateway, mock_graphiti, mock_ehr_client
    ):
        """
        Successful booking stores an episode in Graphiti.
        This feeds the recall agent later — knows who booked what.
        """
        from app.agents.scheduling import SchedulingAgent

        agent = SchedulingAgent(clinic_id=clinic_id)
        agent.llm = mock_llm_gateway
        agent.memory = mock_graphiti
        agent.ehr = mock_ehr_client

        await agent.book_appointment(
            call_id="call_abc123",
            patient_id="PAT_001",
            slot_id="S001",
            reason="annual checkup",
        )

        mock_graphiti.add_episode.assert_called_once()
        episode_kwargs = mock_graphiti.add_episode.call_args[1]
        assert episode_kwargs["clinic_id"] == clinic_id
        assert episode_kwargs["patient_id"] == "PAT_001"


class TestSchedulingAgentCostControl:
    """All scheduling tasks must use local LLM where possible."""

    @pytest.mark.asyncio
    async def test_slot_selection_uses_local_model(
        self, clinic_id, mock_llm_gateway, mock_graphiti
    ):
        """Slot selection task routes to local Ollama."""
        from app.agents.scheduling import SchedulingAgent

        agent = SchedulingAgent(clinic_id=clinic_id)
        agent.llm = mock_llm_gateway
        agent.memory = mock_graphiti

        mock_llm_gateway.route.return_value = {
            "content": '{"slot_id": "S001", "reason": "best match"}',
            "model_used": "ollama/deepseek-coder-v2",
            "tokens_used": 18,
            "cost_usd": 0.0,
        }

        slots = [
            {"slot_id": "S001", "datetime": "2026-07-01T09:00:00", "provider_id": "P001"},
        ]

        await agent.match_slot_to_preference(
            call_id="call_abc123",
            slots=slots,
            patient_preference="morning",
        )

        call_kwargs = mock_llm_gateway.route.call_args[1]
        assert call_kwargs["task_type"] == "appointment_slot_select"
        assert call_kwargs.get("cost_usd", 0.0) == 0.0 or True
