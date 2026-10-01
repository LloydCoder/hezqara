from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from sqlalchemy import text

@dataclass(frozen=True)
class Readiness:
    status:str
    checks:dict[str,str]

async def readiness(session)->Readiness:
    checks:dict[str,str]={}
    try:await session.execute(text("select 1"));checks["database"]="ok"
    except Exception:checks["database"]="unavailable"
    try:await session.execute(text("select to_regclass('public.platform_settings')"));checks["schema"]="ok"
    except Exception:checks["schema"]="unavailable"
    return Readiness("ready" if all(v=="ok" for v in checks.values()) else "degraded",checks)

async def security_posture(session,tenant_id:str)->dict[str,Any]:
    clinic=await session.scalar(text("select id from clinics where clerk_org_id=:org"),{"org":tenant_id})
    if not clinic:raise ValueError("organization clinic is not provisioned")
    row=(await session.execute(text("select ai_enabled,force_human_approval,force_deterministic_fallback,tool_access_enabled,updated_at from ai_control_state where clinic_id=:clinic"),{"clinic":clinic})).mappings().first()
    return {"tenant_id":tenant_id,"ai_controls":dict(row) if row else {"ai_enabled":True,"force_human_approval":False,"force_deterministic_fallback":False,"tool_access_enabled":True,"updated_at":None},"generated_at":datetime.now(timezone.utc)}
