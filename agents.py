"""Agents router — agent status, toggle, and management."""
from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse
from app.agents.base_agent import BaseAgent
from app.agents.reception import ReceptionAgent
from app.agents.scheduling import SchedulingAgent
from app.agents.intake import IntakeAgent
from app.agents.insurance import InsuranceAgent
from app.agents.prior_auth import PriorAuthAgent
from app.agents.refill import RefillAgent
from app.agents.records import RecordsAgent
from app.agents.referrals import ReferralsAgent
from app.agents.recall import RecallAgent
from app.agents.email_agent import EmailAgent
from typing import Optional
import logging

router = APIRouter(prefix="/agents", tags=["agents"])
logger = logging.getLogger(__name__)

AGENT_REGISTRY = {
    "reception": {"class": ReceptionAgent, "description": "Answers every inbound call"},
    "scheduling": {"class": SchedulingAgent, "description": "Books appointments in EHR"},
    "intake": {"class": IntakeAgent, "description": "Collects patient demographics + insurance"},
    "insurance": {"class": InsuranceAgent, "description": "Verifies eligibility and benefits"},
    "prior_auth": {"class": PriorAuthAgent, "description": "Submits prior auth requests"},
    "refill": {"class": RefillAgent, "description": "Processes medication refills"},
    "records": {"class": RecordsAgent, "description": "Releases medical records"},
    "referrals": {"class": ReferralsAgent, "description": "Creates specialist referrals"},
    "recall": {"class": RecallAgent, "description": "Sends recall campaigns"},
    "email": {"class": EmailAgent, "description": "Triages clinic email inbox"},
}


def _agent_status(agent_id: str, clinic_id: str) -> dict:
    """Build agent status dict for API response."""
    info = AGENT_REGISTRY.get(agent_id, {})
    return {
        "id": agent_id,
        "name": agent_id.replace("_", " ").title(),
        "description": info.get("description", ""),
        "status": "idle",
        "calls_handled_today": 0,
        "avg_handle_time_seconds": 0,
        "success_rate": 1.0,
        "cost_today_usd": 0.0,
        "last_action_at": None,
    }


@router.get("")
async def list_agents(clinic_id: str = Query(...)) -> JSONResponse:
    """List all agents and their current status."""
    agents = [_agent_status(aid, clinic_id) for aid in AGENT_REGISTRY]
    return JSONResponse(content=agents)


@router.get("/{agent_type}")
async def get_agent(agent_type: str, clinic_id: str = Query(...)) -> JSONResponse:
    if agent_type not in AGENT_REGISTRY:
        return JSONResponse(status_code=404, content={"error": f"Unknown agent: {agent_type}"})
    return JSONResponse(content=_agent_status(agent_type, clinic_id))


@router.post("/{agent_type}/toggle")
async def toggle_agent(agent_type: str, body: dict) -> JSONResponse:
    """Enable or disable an agent for a clinic."""
    if agent_type not in AGENT_REGISTRY:
        return JSONResponse(status_code=404, content={"error": "Unknown agent"})
    clinic_id = body.get("clinic_id", "")
    enabled = body.get("enabled", True)
    logger.info("Agent %s %s for clinic %s", agent_type, "enabled" if enabled else "disabled", clinic_id)
    return JSONResponse(content={"agent_type": agent_type, "enabled": enabled, "updated": True})
