from __future__ import annotations
from sqlalchemy import text

async def get_limits(session, tenant_id: str) -> dict:
    row = (await session.execute(text("""
        select plan_code, monthly_executions, monthly_voice_minutes,
               monthly_messages, max_users, max_locations
        from tenant_limits where clinic_id=:tenant
    """), {"tenant": tenant_id})).mappings().first()
    if row:
        return dict(row)
    return {
        "plan_code": "starter", "monthly_executions": 1000,
        "monthly_voice_minutes": 500, "monthly_messages": 5000,
        "max_users": 5, "max_locations": 1,
    }

async def record_usage(session, tenant_id: str, metric: str, amount: int = 1) -> dict:
    if amount <= 0:
        raise ValueError("usage amount must be positive")
    await session.execute(text("""
        insert into platform_usage_daily(clinic_id,usage_date,metric,quantity)
        values(:tenant,current_date,:metric,:amount)
        on conflict (clinic_id,usage_date,metric)
        do update set quantity=platform_usage_daily.quantity+excluded.quantity
    """), {"tenant": tenant_id, "metric": metric, "amount": amount})
    row = (await session.execute(text("""
        select usage_date,metric,quantity from platform_usage_daily
        where clinic_id=:tenant and usage_date=current_date and metric=:metric
    """), {"tenant": tenant_id, "metric": metric})).mappings().first()
    return dict(row)

async def current_usage(session, tenant_id: str) -> list[dict]:
    rows = await session.execute(text("""
        select metric,sum(quantity)::bigint quantity
        from platform_usage_daily where clinic_id=:tenant
        and usage_date >= date_trunc('month',current_date)::date
        group by metric order by metric
    """), {"tenant": tenant_id})
    return [dict(r._mapping) for r in rows]
