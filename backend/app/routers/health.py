"""Liveness endpoint used by load balancers and monitoring."""
from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check() -> JSONResponse:
    return JSONResponse(
        content={
            "status": "ok",
            "service": "hezqara-ai",
            "version": "1.0.0",
            "port": 8004,
        }
    )


@router.get("/")
async def root() -> JSONResponse:
    return JSONResponse(content={"service": "HEZQARA AI", "status": "running"})
