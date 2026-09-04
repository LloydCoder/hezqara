"""Health check endpoint — used by ResilientAI monitoring."""
from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check() -> JSONResponse:
    return JSONResponse(content={
        "status": "ok",
        "service": "carenova-ai",
        "version": "0.1.0",
        "port": 8004,
    })


@router.get("/")
async def root() -> JSONResponse:
    return JSONResponse(content={"service": "Carenova AI", "status": "running"})
