"""Recalls router."""
from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse
router = APIRouter(prefix="/recalls", tags=["recalls"])

@router.get("")
async def list_recalls(clinic_id: str = Query(...)) -> JSONResponse:
    return JSONResponse(content=[])

@router.post("/launch")
async def launch_recall(body: dict) -> JSONResponse:
    return JSONResponse(content={"launched": True, "campaign_id": "camp_001"})
