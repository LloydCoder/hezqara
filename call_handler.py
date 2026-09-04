"""
Call Handler — bridges Retell AI events to Carenova agents.
Creates correct agent per clinic and routes events.
Injects stub dependencies when real services are not configured.
"""
import logging
from typing import Optional
from unittest.mock import AsyncMock

from app.agents.reception import ReceptionAgent

logger = logging.getLogger(__name__)


def _stub_memory():
    """Stub Graphiti client for when memory service is not yet configured."""
    memory = AsyncMock()
    memory.get_clinic_context = AsyncMock(return_value={
        "clinic_id": "unknown",
        "clinic_name": "Family Care Clinic",
        "ehr": "athenahealth",
        "active_agents": ["reception"],
    })
    memory.add_episode = AsyncMock(return_value={"episode_id": None})
    return memory


def _stub_llm():
    """Stub LLM gateway for when LLM is not configured."""
    llm = AsyncMock()
    llm.route = AsyncMock(return_value={
        "content": "Thank you for calling. How can I help you today?",
        "model_used": "stub",
        "tokens_used": 0,
        "cost_usd": 0.0,
    })
    return llm


class CallHandler:
    """Routes inbound call events to the correct agent."""

    async def handle_call_started(
        self,
        call_id: str,
        from_number: str,
        clinic_id: str,
        llm=None,
        memory=None,
    ) -> dict:
        """Create Reception Agent and handle call start."""
        agent = ReceptionAgent(
            clinic_id=clinic_id,
            llm=llm or _stub_llm(),
            memory=memory or _stub_memory(),
        )
        return await agent.handle_call_started(
            call_id=call_id,
            from_number=from_number,
        )

    async def handle_call_ended(
        self,
        call_data: dict,
        clinic_id: str,
        llm=None,
        memory=None,
    ) -> dict:
        """Create Reception Agent and handle call end."""
        agent = ReceptionAgent(
            clinic_id=clinic_id,
            llm=llm or _stub_llm(),
            memory=memory or _stub_memory(),
        )
        return await agent.handle_call_ended(call_data=call_data)
