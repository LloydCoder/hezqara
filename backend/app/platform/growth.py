from __future__ import annotations
from sqlalchemy import text

ONBOARDING_STEPS=("clinic_profile","users","ai_controls","communications","billing","first_workflow")

async def _clinic_id(session,organization_id:str)->str:
    clinic=await session.scalar(text("select id from clinics where clerk_org_id=:org"),{"org":organization_id})
    if not clinic:raise ValueError("organization clinic is not provisioned")
    return str(clinic)

async def onboarding_status(session,tenant_id:str)->dict:
    clinic=await _clinic_id(session,tenant_id)
    rows=await session.execute(text("select step,status,completed_at from onboarding_checklist where clinic_id=:clinic order by step"),{"clinic":clinic})
    items=[dict(r._mapping) for r in rows]; known={x["step"] for x in items}
    items.extend({"step":step,"status":"pending","completed_at":None} for step in ONBOARDING_STEPS if step not in known)
    completed=sum(x["status"]=="completed" for x in items)
    return {"steps":items,"completed":completed,"total":len(ONBOARDING_STEPS),"percent":round(completed*100/len(ONBOARDING_STEPS))}

async def complete_onboarding_step(session,tenant_id:str,step:str,actor:str)->dict:
    if step not in ONBOARDING_STEPS:raise ValueError("unknown onboarding step")
    clinic=await _clinic_id(session,tenant_id)
    await session.execute(text("insert into onboarding_checklist(clinic_id,step,status,completed_at,completed_by) values(:clinic,:step,'completed',now(),:actor) on conflict (clinic_id,step) do update set status='completed',completed_at=now(),completed_by=:actor"),{"clinic":clinic,"step":step,"actor":actor})
    return await onboarding_status(session,tenant_id)

async def create_lead(session,tenant_id:str,email:str,clinic_name:str|None,source:str,campaign:str|None)->dict:
    clinic=await _clinic_id(session,tenant_id)
    row=(await session.execute(text("insert into growth_leads(clinic_id,email,clinic_name,source,campaign) values(:clinic,:email,:name,:source,:campaign) on conflict (clinic_id,email) do update set clinic_name=coalesce(excluded.clinic_name,growth_leads.clinic_name),source=excluded.source,campaign=excluded.campaign,updated_at=now() returning id,clinic_id,email,clinic_name,source,campaign,status,created_at"),{"clinic":clinic,"email":email.lower().strip(),"name":clinic_name,"source":source,"campaign":campaign})).mappings().first()
    if not row:raise ValueError("lead could not be created")
    return dict(row)
