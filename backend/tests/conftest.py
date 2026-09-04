"""
Carenova Test Fixtures
Shared across all test modules.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from typing import AsyncGenerator


# ── Clinic fixture ────────────────────────────────────────────────────────────

@pytest.fixture
def clinic_id() -> str:
    return "clinic_test_001"


@pytest.fixture
def clinic_context() -> dict:
    return {
        "clinic_id": "clinic_test_001",
        "clinic_name": "Family Care Associates",
        "ehr": "athenahealth",
        "practice_id": "195900",
        "timezone": "America/New_York",
        "active_agents": ["reception", "scheduling", "insurance"],
        "providers": [
            {"id": "P001", "name": "Dr. Sarah Chen", "specialty": "Family Medicine"},
            {"id": "P002", "name": "Dr. Marcus Webb", "specialty": "Internal Medicine"},
        ],
        "hours": {
            "monday": {"open": "08:00", "close": "17:00"},
            "tuesday": {"open": "08:00", "close": "17:00"},
            "wednesday": {"open": "08:00", "close": "17:00"},
            "thursday": {"open": "08:00", "close": "17:00"},
            "friday": {"open": "08:00", "close": "16:00"},
        },
    }


# ── Patient fixture ───────────────────────────────────────────────────────────

@pytest.fixture
def patient_data() -> dict:
    return {
        "first_name": "Maria",
        "last_name": "Santos",
        "date_of_birth": "1985-03-15",
        "phone": "+12125551234",
        "insurance": "BlueCross BlueShield",
        "member_id": "BCB123456789",
    }


# ── Mock LLM Gateway ──────────────────────────────────────────────────────────

@pytest.fixture
def mock_llm_gateway():
    gateway = AsyncMock()
    gateway.route = AsyncMock(return_value={
        "content": "How can I help you today?",
        "model_used": "ollama/deepseek-coder-v2",
        "tokens_used": 45,
        "cost_usd": 0.0,
    })
    return gateway


# ── Mock Retell Client ────────────────────────────────────────────────────────

@pytest.fixture
def mock_retell_client():
    client = AsyncMock()
    client.create_call = AsyncMock(return_value={
        "call_id": "call_test_abc123",
        "status": "registered",
    })
    client.end_call = AsyncMock(return_value={"status": "ended"})
    return client


# ── Mock Graphiti Client ──────────────────────────────────────────────────────

@pytest.fixture
def mock_graphiti():
    graphiti = AsyncMock()
    graphiti.get_clinic_context = AsyncMock(return_value={
        "clinic_id": "clinic_test_001",
        "ehr": "athenahealth",
        "last_interaction": None,
        "patient_count": 0,
    })
    graphiti.add_episode = AsyncMock(return_value={"episode_id": "ep_001"})
    graphiti.search = AsyncMock(return_value=[])
    return graphiti


# ── Mock EHR Client ───────────────────────────────────────────────────────────

@pytest.fixture
def mock_ehr_client():
    client = AsyncMock()
    client.get_available_slots = AsyncMock(return_value=[
        {"slot_id": "S001", "datetime": "2026-07-01T09:00:00", "provider_id": "P001"},
        {"slot_id": "S002", "datetime": "2026-07-01T10:30:00", "provider_id": "P001"},
        {"slot_id": "S003", "datetime": "2026-07-01T14:00:00", "provider_id": "P002"},
    ])
    client.book_appointment = AsyncMock(return_value={
        "appointment_id": "APT_001",
        "status": "confirmed",
        "datetime": "2026-07-01T09:00:00",
        "provider": "Dr. Sarah Chen",
    })
    client.get_patient = AsyncMock(return_value=None)
    client.create_patient = AsyncMock(return_value={"patient_id": "PAT_001"})
    return client


# ── Sample call payloads ──────────────────────────────────────────────────────

@pytest.fixture
def retell_call_started_payload() -> dict:
    return {
        "event": "call_started",
        "call": {
            "call_id": "call_abc123",
            "call_type": "inbound",
            "from_number": "+12125551234",
            "to_number": "+18885550001",
            "metadata": {"clinic_id": "clinic_test_001"},
        },
    }


@pytest.fixture
def retell_call_ended_payload() -> dict:
    return {
        "event": "call_ended",
        "call": {
            "call_id": "call_abc123",
            "call_type": "inbound",
            "from_number": "+12125551234",
            "to_number": "+18885550001",
            "duration_ms": 187000,
            "transcript": [
                {"role": "agent", "content": "Thank you for calling Family Care. How can I help?"},
                {"role": "user", "content": "I need to schedule an appointment with Dr. Chen."},
                {"role": "agent", "content": "Of course. What day works best for you?"},
                {"role": "user", "content": "Next Tuesday morning if possible."},
            ],
            "metadata": {"clinic_id": "clinic_test_001"},
        },
    }


@pytest.fixture
def retell_transcript_payload() -> dict:
    return {
        "event": "transcript",
        "call_id": "call_abc123",
        "transcript": [
            {"role": "user", "content": "I need to book an appointment."},
        ],
        "metadata": {"clinic_id": "clinic_test_001"},
    }
