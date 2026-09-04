"""Calls router — real Supabase queries."""
from fastapi import APIRouter, Query, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.services.database import get_db
from app.models.call import Call
from app.models.patient import Patient

router = APIRouter(prefix="/calls", tags=["calls"])


@router.get("")
async def list_calls(
    clinic_id: str = Query(...),
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    try:
        stmt = (
            select(Call, Patient.first_name, Patient.last_name)
            .join(Patient, Call.patient_id == Patient.id, isouter=True)
            .where(Call.clinic_id == clinic_id)
            .order_by(Call.started_at.desc())
            .limit(limit)
        )
        result = await db.execute(stmt)
        rows = result.all()
        return JSONResponse(content=[
            {
                "id": row.Call.id, "clinic_id": row.Call.clinic_id,
                "patient_id": row.Call.patient_id,
                "patient_name": f"{row.first_name or ''} {row.last_name or ''}".strip() or None,
                "retell_call_id": row.Call.retell_call_id,
                "call_type": row.Call.call_type,
                "from_number": None,  # Never expose raw phone in API
                "duration_ms": row.Call.duration_ms,
                "intent": row.Call.intent,
                "outcome": row.Call.outcome,
                "agent_type": row.Call.agent_type,
                "started_at": row.Call.started_at.isoformat() if row.Call.started_at else None,
                "ended_at": row.Call.ended_at.isoformat() if row.Call.ended_at else None,
            }
            for row in rows
        ])
    except Exception as e:
        return JSONResponse(content=[], headers={"X-DB-Error": str(e)[:100]})


@router.get("/{call_id}")
async def get_call(call_id: str, db: AsyncSession = Depends(get_db)) -> JSONResponse:
    result = await db.execute(select(Call).where(Call.id == call_id))
    call = result.scalar_one_or_none()
    if not call:
        return JSONResponse(status_code=404, content={"error": "Call not found"})
    return JSONResponse(content={
        "id": call.id, "agent_type": call.agent_type,
        "intent": call.intent, "duration_ms": call.duration_ms,
        "transcript": call.transcript or [],
    })
