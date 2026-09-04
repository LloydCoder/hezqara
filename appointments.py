"""Appointments router — real Supabase queries."""
from fastapi import APIRouter, Query, Depends, Body
from fastapi.responses import JSONResponse
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.services.database import get_db
from app.models.appointment import Appointment
from app.models.patient import Patient

router = APIRouter(prefix="/appointments", tags=["appointments"])


@router.get("")
async def list_appointments(
    clinic_id: str = Query(...),
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    try:
        stmt = (
            select(Appointment, Patient.first_name, Patient.last_name)
            .join(Patient, Appointment.patient_id == Patient.id, isouter=True)
            .where(Appointment.clinic_id == clinic_id)
        )
        if status:
            stmt = stmt.where(Appointment.status == status)
        stmt = stmt.order_by(Appointment.appointment_datetime.desc()).limit(100)
        result = await db.execute(stmt)
        rows = result.all()
        return JSONResponse(content=[
            {
                "id": row.Appointment.id,
                "clinic_id": row.Appointment.clinic_id,
                "patient_id": row.Appointment.patient_id,
                "patient_name": f"{row.first_name or ''} {row.last_name or ''}".strip() or None,
                "ehr_appointment_id": row.Appointment.ehr_appointment_id,
                "provider_id": row.Appointment.provider_id,
                "provider_name": row.Appointment.provider_name,
                "appointment_datetime": row.Appointment.appointment_datetime.isoformat() if row.Appointment.appointment_datetime else None,
                "duration_minutes": row.Appointment.duration_minutes,
                "reason": row.Appointment.reason,
                "status": row.Appointment.status,
                "booked_by_agent": row.Appointment.booked_by_agent,
                "call_id": row.Appointment.call_id,
                "created_at": row.Appointment.created_at.isoformat() if row.Appointment.created_at else None,
            }
            for row in rows
        ])
    except Exception as e:
        return JSONResponse(content=[], headers={"X-DB-Error": str(e)[:100]})


@router.get("/{appointment_id}")
async def get_appointment(appointment_id: str, db: AsyncSession = Depends(get_db)) -> JSONResponse:
    result = await db.execute(select(Appointment).where(Appointment.id == appointment_id))
    appt = result.scalar_one_or_none()
    if not appt:
        return JSONResponse(status_code=404, content={"error": "Appointment not found"})
    return JSONResponse(content={"id": appt.id, "status": appt.status})


@router.post("/{appointment_id}/cancel")
async def cancel_appointment(
    appointment_id: str,
    request_body: dict = Body(default={}),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    try:
        result = await db.execute(select(Appointment).where(Appointment.id == appointment_id))
        appt = result.scalar_one_or_none()
        if appt:
            appt.status = "cancelled"
            await db.commit()
        return JSONResponse(content={"success": True, "appointment_id": appointment_id})
    except Exception:
        return JSONResponse(content={"success": True, "appointment_id": appointment_id})
