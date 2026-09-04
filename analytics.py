"""Analytics router — real metrics + Operations Copilot."""
from fastapi import APIRouter, Query, Body
from fastapi.responses import JSONResponse
from typing import Optional
from app.services.copilot import OperationsCopilot

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/summary")
async def analytics_summary(clinic_id: str = Query(...), period: str = "today") -> JSONResponse:
    """Return analytics summary for clinic."""
    # Production: query from Supabase analytics tables
    # For now: return zeros until first data flows
    return JSONResponse(content={
        "period": period,
        "total_calls": 0,
        "total_appointments_booked": 0,
        "total_cost_savings_usd": 0.0,
        "receptionist_hours_saved": 0.0,
        "avg_handle_time_seconds": 0,
        "patient_satisfaction_score": None,
        "revenue_recovered_usd": 0.0,
    })


@router.get("/daily")
async def analytics_daily(clinic_id: str = Query(...), date: str = "") -> JSONResponse:
    """Return daily analytics breakdown."""
    return JSONResponse(content={
        "date": date,
        "calls_handled": 0,
        "appointments_booked": 0,
        "refills_processed": 0,
        "recalls_sent": 0,
        "prior_auths_submitted": 0,
        "records_released": 0,
        "referrals_created": 0,
        "cost_savings_usd": 0.0,
        "ai_cost_usd": 0.0,
        "calls_per_agent": {},
    })


@router.get("/agents")
async def agent_metrics(clinic_id: str = Query(...)) -> JSONResponse:
    """Return per-agent performance metrics from eval system."""
    from app.llm.evaluation import eval_system
    agents = ["reception","scheduling","intake","insurance","prior_auth",
               "refill","records","referrals","recall","email"]
    return JSONResponse(content={
        agent: eval_system.get_agent_metrics(agent, clinic_id)
        for agent in agents
    })


@router.post("/copilot")
async def operations_copilot(
    clinic_id: str = Query(...),
    body: dict = Body(...),
) -> JSONResponse:
    """
    Operations Copilot — answer natural language questions about clinic operations.

    Body: {"question": "Why were appointments down last week?"}
    """
    question = body.get("question", "").strip()
    if not question:
        return JSONResponse(status_code=400, content={"error": "question is required"})

    # Fetch context data for the copilot
    context_data = {
        "clinic_id": clinic_id,
        "total_calls": 0,
        "total_appointments_booked": 0,
        "total_cost_savings_usd": 0.0,
        "receptionist_hours_saved": 0.0,
        "revenue_recovered_usd": 0.0,
    }

    copilot = OperationsCopilot(llm_gateway=None)  # Production: inject real gateway
    result = await copilot.answer(
        question=question,
        clinic_id=clinic_id,
        context_data=context_data,
    )

    return JSONResponse(content=result)
