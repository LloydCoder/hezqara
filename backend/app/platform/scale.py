from __future__ import annotations
from sqlalchemy import text

async def _clinic_id(session, organization_id: str) -> str:
    clinic = await session.scalar(text("select id from clinics where clerk_org_id=:org"), {"org": organization_id})
    if not clinic: raise ValueError("organization clinic is not provisioned")
    return str(clinic)

async def get_limits(session, tenant_id: str) -> dict:
    clinic = await _clinic_id(session, tenant_id)
    row = (await session.execute(text("select plan_code,monthly_executions,monthly_voice_minutes,monthly_messages,max_users,max_locations from tenant_limits where clinic_id=:clinic"), {"clinic": clinic})).mappings().first()
    if row: return dict(row)
    return {"plan_code":"starter","monthly_executions":1000,"monthly_voice_minutes":500,"monthly_messages":5000,"max_users":5,"max_locations":1}

async def record_usage(session, tenant_id: str, metric: str, amount: int = 1) -> dict:
    if amount <= 0: raise ValueError("usage amount must be positive")
    clinic = await _clinic_id(session, tenant_id)
    await session.execute(text("""insert into platform_usage_daily(clinic_id,usage_date,metric,quantity) values(:clinic,current_date,:metric,:amount) on conflict (clinic_id,usage_date,metric) do update set quantity=platform_usage_daily.quantity+excluded.quantity"""), {"clinic":clinic,"metric":metric,"amount":amount})
    row = (await session.execute(text("select usage_date,metric,quantity from platform_usage_daily where clinic_id=:clinic and usage_date=current_date and metric=:metric"), {"clinic":clinic,"metric":metric})).mappings().first()
    return dict(row)

async def current_usage(session, tenant_id: str) -> list[dict]:
    clinic = await _clinic_id(session, tenant_id)
    rows = await session.execute(text("select metric,sum(quantity)::bigint quantity from platform_usage_daily where clinic_id=:clinic and usage_date>=date_trunc('month',current_date)::date group by metric order by metric"), {"clinic":clinic})
    return [dict(r._mapping) for r in rows]
