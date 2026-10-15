from fastapi import APIRouter
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from app.infrastructure.database import system_session_context
from app.platform.reliability import readiness

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict[str, str]:
    """Process liveness only; deliberately independent of infrastructure."""
    return {"status": "ok", "service": "hezqara-api"}


@router.get("/ready")
async def ready() -> JSONResponse:
    """Report dependency readiness without exposing credentials or infrastructure details."""
    try:
        async with system_session_context() as session:
            result = await readiness(session)
    except Exception:
        # A missing DATABASE_URL, failed connection, or unavailable schema must
        # fail closed. Do not turn an API process that cannot serve work into ready.
        result = {
            "status": "degraded",
            "checks": {
                "database": "unavailable",
                "durable_jobs": "unavailable",
                "worker_heartbeat": "unavailable",
            },
        }

    checks = result.get("checks", {})
    is_ready = (
        result.get("status") == "ready"
        and bool(checks)
        and all(value == "ok" for value in checks.values())
    )
    if not is_ready:
        result["status"] = "degraded"

    return JSONResponse(
        content=jsonable_encoder(result),
        status_code=200 if is_ready else 503,
        headers={"Cache-Control": "no-store"},
    )
