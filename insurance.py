"""Insurance router."""
from fastapi import APIRouter
from fastapi.responses import JSONResponse
router = APIRouter(prefix="/insurance", tags=["insurance"])

@router.post("/verify")
async def verify_insurance(body: dict) -> JSONResponse:
    return JSONResponse(content={
        "eligible": None, "carrier": None,
        "copay_primary_care": None, "deductible_remaining": None,
        "status": "pending_ehr_connection"
    })
