from __future__ import annotations

from sqlalchemy import text

ONBOARDING_STEPS = (
    "clinic_profile",
    "users",
    "ai_controls",
    "communications",
    "billing",
    "first_workflow",
)

async def onboarding_status(session, tenant_id: str) -> dict:
    rows = await session.execute(
        text(
            """
            select step,status,completed_at from onboarding_checklist
            where clinic_id=:tenant order by step
            """
        ),
        {"tenant": tenant_id},
    )
    items = [dict(r._mapping) for r in rows]
    known = {x["step"] for x in items}
    for step in ONBOARDING_STEPS:
        if step not in known:
            items.append({"step": step, "status": "pending", "completed_at": None})
    completed = sum(x["status"] == "completed" for x in items)
    return {
        "steps": items,
        "completed": completed,
        "total": len(ONBOARDING_STEPS),
        "percent": round(completed * 100 / len(ONBOARDING_STEPS)),
    }

async def complete_onboarding_step(session, tenant_id: str, step: str, actor: str) -> dict:
    if step not in ONBOARDING_STEPS:
        raise ValueError("unknown onboarding step")
    await session.execute(
        text(
            """
            insert into onboarding_checklist(clinic_id,step,status,completed_at,completed_by)
            values(:tenant,:step,'completed',now(),:actor)
            on conflict (clinic_id,step) do update set status='completed',completed_at=now(),completed_by=:actor
            """
        ),
        {"tenant": tenant_id, "step": step, "actor": actor},
    )
    return await onboarding_status(session, tenant_id)

async def create_lead(
    session,
    tenant_id: str,
    email: str,
    clinic_name: str | None,
    source: str,
    campaign: str | None,
) -> dict:
    row = (
        await session.execute(
            text(
                """
                insert into growth_leads(clinic_id,email,clinic_name,source,campaign)
                values(:tenant,:email,:clinic,:source,:campaign)
                on conflict (clinic_id,email) do update set
                  clinic_name=coalesce(excluded.clinic_name,growth_leads.clinic_name),
                  source=excluded.source,
                  campaign=excluded.campaign,
                  updated_at=now()
                returning id,clinic_id,email,clinic_name,source,campaign,status,created_at
                """
            ),
            {
                "tenant": tenant_id,
                "email": email.lower().strip(),
                "clinic": clinic_name,
                "source": source,
                "campaign": campaign,
            },
        )
    ).mappings().first()
    return dict(row)
