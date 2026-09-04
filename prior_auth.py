"""Prior Auth router."""
from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse
from typing import Optional
router = APIRouter(prefix="/prior-auth", tags=["prior_auth"])

@router.get("")
async def list_prior_auths(clinic_id: str = Query(...), status: Optional[str] = None) -> JSONResponse:
    return JSONResponse(content=[])

@router.get("/{tracking_number}/status")
async def get_pa_status(tracking_number: str) -> JSONResponse:
    return JSONResponse(content={"tracking_number": tracking_number, "status": "pending"})
