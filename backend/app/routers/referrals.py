"""Referrals router."""
from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse
router = APIRouter(prefix="/referrals", tags=["referrals"])

@router.get("")
async def list_referrals(clinic_id: str = Query(...)) -> JSONResponse:
    return JSONResponse(content=[])
