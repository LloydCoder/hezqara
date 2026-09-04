"""Patients router — real Supabase queries."""
from fastapi import APIRouter, Query, Depends
from fastapi.responses import JSONResponse
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from app.services.database import get_db
from app.models.patient import Patient

router = APIRouter(prefix="/patients", tags=["patients"])


@router.get("")
async def list_patients(
    clinic_id: str = Query(...),
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    try:
        stmt = select(Patient).where(Patient.clinic_id == clinic_id)
        if search:
            stmt = stmt.where(or_(
                Patient.first_name.ilike(f"%{search}%"),
                Patient.last_name.ilike(f"%{search}%"),
                Patient.phone.ilike(f"%{search}%"),
            ))
        stmt = stmt.order_by(Patient.created_at.desc()).limit(100)
        result = await db.execute(stmt)
        patients = result.scalars().all()
        return JSONResponse(content=[
            {
                "id": p.id, "clinic_id": p.clinic_id,
                "ehr_patient_id": p.ehr_patient_id,
                "first_name": p.first_name, "last_name": p.last_name,
                "date_of_birth": p.date_of_birth.isoformat() if p.date_of_birth else None,
                "phone": p.phone, "email": p.email,
                "insurance_carrier": p.insurance_carrier,
                "insurance_member_id": p.insurance_member_id,
                "uninsured": p.uninsured,
                "created_at": p.created_at.isoformat() if p.created_at else None,
            }
            for p in patients
        ])
    except Exception as e:
        return JSONResponse(content=[], headers={"X-DB-Error": str(e)[:100]})


@router.get("/{patient_id}")
async def get_patient(patient_id: str, db: AsyncSession = Depends(get_db)) -> JSONResponse:
    result = await db.execute(select(Patient).where(Patient.id == patient_id))
    patient = result.scalar_one_or_none()
    if not patient:
        return JSONResponse(status_code=404, content={"error": "Patient not found"})
    return JSONResponse(content={"id": patient.id, "first_name": patient.first_name, "last_name": patient.last_name})
