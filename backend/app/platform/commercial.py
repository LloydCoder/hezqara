from __future__ import annotations
from decimal import Decimal
from sqlalchemy import text

PLAN_CATALOG={"starter":{"monthly_price_usd":Decimal("299.00"),"monthly_executions":1000,"monthly_voice_minutes":500,"monthly_messages":5000,"max_users":5,"max_locations":1},"growth":{"monthly_price_usd":Decimal("799.00"),"monthly_executions":5000,"monthly_voice_minutes":2500,"monthly_messages":25000,"max_users":15,"max_locations":3},"professional":{"monthly_price_usd":Decimal("1499.00"),"monthly_executions":15000,"monthly_voice_minutes":7500,"monthly_messages":75000,"max_users":50,"max_locations":10},"enterprise":{"monthly_price_usd":Decimal("3000.00"),"monthly_executions":100000,"monthly_voice_minutes":50000,"monthly_messages":500000,"max_users":500,"max_locations":100}}

def get_plan(plan_code:str)->dict:
    try:return dict(PLAN_CATALOG[plan_code])
    except KeyError as exc:raise ValueError("unknown plan") from exc

async def _clinic_id(session,organization_id:str)->str:
    clinic=await session.scalar(text("select id from clinics where clerk_org_id=:org"),{"org":organization_id})
    if not clinic:raise ValueError("organization clinic is not provisioned")
    return str(clinic)

async def get_subscription(session,tenant_id:str)->dict:
    clinic=await _clinic_id(session,tenant_id)
    row=(await session.execute(text("select plan_code,status,provider,provider_customer_id,provider_subscription_id,current_period_start,current_period_end,cancel_at_period_end from subscriptions where clinic_id=:clinic"),{"clinic":clinic})).mappings().first()
    if row:return dict(row)
    return {"plan_code":"starter","status":"trialing","provider":None,"provider_customer_id":None,"provider_subscription_id":None,"current_period_start":None,"current_period_end":None,"cancel_at_period_end":False}

async def change_plan(session,tenant_id:str,plan_code:str,actor:str)->dict:
    plan=get_plan(plan_code); clinic=await _clinic_id(session,tenant_id)
    await session.execute(text("insert into tenant_limits(clinic_id,plan_code,monthly_executions,monthly_voice_minutes,monthly_messages,max_users,max_locations) values(:clinic,:plan,:executions,:voice,:messages,:users,:locations) on conflict (clinic_id) do update set plan_code=excluded.plan_code,monthly_executions=excluded.monthly_executions,monthly_voice_minutes=excluded.monthly_voice_minutes,monthly_messages=excluded.monthly_messages,max_users=excluded.max_users,max_locations=excluded.max_locations,updated_at=now()"),{"clinic":clinic,"plan":plan_code,"executions":plan["monthly_executions"],"voice":plan["monthly_voice_minutes"],"messages":plan["monthly_messages"],"users":plan["max_users"],"locations":plan["max_locations"]})
    await session.execute(text("insert into subscriptions(clinic_id,plan_code,status,provider) values(:clinic,:plan,'active','manual') on conflict (clinic_id) do update set plan_code=excluded.plan_code,status='active',updated_at=now()"),{"clinic":clinic,"plan":plan_code})
    await session.execute(text("insert into platform_events(clinic_id,event_type,actor_id,payload) values(:clinic,'subscription.plan_changed',:actor,cast(:payload as jsonb))"),{"clinic":clinic,"actor":actor,"payload":'{"plan":"'+plan_code+'"}'})
    return await get_subscription(session,tenant_id)
