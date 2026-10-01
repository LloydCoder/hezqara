from __future__ import annotations

import hashlib
import json
from datetime import date, timedelta

from sqlalchemy import text


ONBOARDING_STEPS = ("clinic_profile", "users", "ai_controls", "communications", "billing", "first_workflow")


async def _clinic_id(session, organization_id: str) -> str:
    clinic = await session.scalar(text("select id from clinics where clerk_org_id=:org"), {"org": organization_id})
    if not clinic:
        raise ValueError("organization clinic is not provisioned")
    return str(clinic)


async def _ensure_state(session, clinic: str, actor: str) -> dict:
    await session.execute(
        text(
            """
            insert into clinic_activation(clinic_id,updated_by)
            values(:clinic,:actor)
            on conflict (clinic_id) do nothing
            """
        ),
        {"clinic": clinic, "actor": actor},
    )
    row = (await session.execute(text("select * from clinic_activation where clinic_id=:clinic"), {"clinic": clinic})).mappings().one()
    return dict(row)


async def preflight(session, organization_id: str, actor: str) -> dict:
    clinic = await _clinic_id(session, organization_id)
    checks: list[dict] = []

    async def check(code: str, ok: bool, detail: dict) -> None:
        checks.append({"code": code, "status": "passed" if ok else "failed", "detail": detail})
        await session.execute(
            text(
                "insert into activation_evidence(clinic_id,check_code,status,detail,actor_id) values(:clinic,:code,:status,cast(:detail as jsonb),:actor)"
            ),
            {"clinic": clinic, "code": code, "status": "passed" if ok else "failed", "detail": json.dumps(detail), "actor": actor},
        )

    clinic_row = (await session.execute(text("select id,name from clinics where id=:clinic"), {"clinic": clinic})).mappings().one()
    await check("tenant", bool(clinic_row["id"]), {"clinic_id": clinic})

    onboarding = (
        await session.execute(
            text("select count(*) filter (where status='completed') completed from onboarding_checklist where clinic_id=:clinic"),
            {"clinic": clinic},
        )
    ).scalar() or 0
    await check("onboarding", int(onboarding) >= len(ONBOARDING_STEPS), {"completed": int(onboarding), "required": len(ONBOARDING_STEPS)})

    integration = (
        await session.execute(
            text("select count(*) from integrations where clinic_id=:clinic and enabled=true and status in ('healthy','connected')"),
            {"clinic": clinic},
        )
    ).scalar() or 0
    await check("integration", int(integration) > 0, {"healthy_integrations": int(integration)})

    ai = (
        await session.execute(
            text("select ai_enabled from ai_control_state where clinic_id=:clinic"),
            {"clinic": clinic},
        )
    ).scalar_one_or_none()
    await check("ai_governance", ai is True, {"ai_enabled": ai})

    subscription = (
        await session.execute(
            text("select status from subscriptions where clinic_id=:clinic"),
            {"clinic": clinic},
        )
    ).scalar_one_or_none()
    await check("commercial", subscription in {"trialing", "active"}, {"status": subscription})

    workflows = (
        await session.execute(
            text("select count(*) from workflows where clinic_id=:clinic and status='active'"),
            {"clinic": clinic},
        )
    ).scalar() or 0
    await check("workflow", int(workflows) > 0, {"active_workflows": int(workflows)})

    passed = all(item["status"] == "passed" for item in checks)
    await session.execute(
        text(
            """
            insert into clinic_activation(clinic_id,state,last_tested_at,updated_by)
            values(:clinic,case when :passed then 'ready' else 'testing' end,now(),:actor)
            on conflict (clinic_id) do update set state=case when :passed then 'ready' else 'testing' end,last_tested_at=now(),updated_by=:actor,updated_at=now()
            """
        ),
        {"clinic": clinic, "passed": passed, "actor": actor},
    )
    return {"clinic_id": clinic, "ready": passed, "checks": checks}


async def activate(session, organization_id: str, actor: str) -> dict:
    result = await preflight(session, organization_id, actor)
    if not result["ready"]:
        raise ValueError("clinic activation preflight failed")
    clinic = result["clinic_id"]
    await session.execute(
        text(
            """
            update clinic_activation
            set previous_state=state,state='active',activated_at=now(),updated_by=:actor,updated_at=now()
            where clinic_id=:clinic
            """
        ),
        {"clinic": clinic, "actor": actor},
    )
    return await state(session, organization_id)


async def state(session, organization_id: str) -> dict:
    clinic = await _clinic_id(session, organization_id)
    row = (await session.execute(text("select * from clinic_activation where clinic_id=:clinic"), {"clinic": clinic})).mappings().first()
    return dict(row) if row else await _ensure_state(session, clinic, "system")


async def set_state(session, organization_id: str, target: str, actor: str) -> dict:
    allowed = {"paused", "disabled", "recovering"}
    if target not in allowed:
        raise ValueError("invalid activation state")
    clinic = await _clinic_id(session, organization_id)
    current = await state(session, organization_id)
    if target == "paused" and current["state"] not in {"active", "ready", "recovered"}:
        raise ValueError("clinic is not active")
    if target == "recovering" and current["state"] not in {"paused", "disabled"}:
        raise ValueError("clinic must be paused or disabled before recovery")
    await session.execute(
        text("update clinic_activation set previous_state=state,state=:target,updated_by=:actor,updated_at=now() where clinic_id=:clinic"),
        {"clinic": clinic, "target": target, "actor": actor},
    )
    if target == "recovering":
        result = await preflight(session, organization_id, actor)
        if result["ready"]:
            await session.execute(
                text("update clinic_activation set state='recovered',last_recovered_at=now(),updated_by=:actor,updated_at=now() where clinic_id=:clinic"),
                {"clinic": clinic, "actor": actor},
            )
    return await state(session, organization_id)


async def rollback(session, organization_id: str, actor: str, reason: str) -> dict:
    clinic = await _clinic_id(session, organization_id)
    current = await state(session, organization_id)
    target = current["previous_state"] or "paused"
    if target not in {"active", "ready", "paused", "disabled"}:
        target = "paused"
    await session.execute(
        text("update clinic_activation set state=:target,previous_state=:previous,updated_by=:actor,updated_at=now() where clinic_id=:clinic"),
        {"clinic": clinic, "target": target, "previous": current["state"], "actor": actor},
    )
    await session.execute(
        text(
            "insert into activation_evidence(clinic_id,check_code,status,detail,actor_id) values(:clinic,'rollback','passed',cast(:detail as jsonb),:actor)"
        ),
        {"clinic": clinic, "detail": json.dumps({"from": current["state"], "to": target, "reason": reason}), "actor": actor},
    )
    return await state(session, organization_id)


async def roi_snapshot(session, organization_id: str, actor: str) -> dict:
    clinic = await _clinic_id(session, organization_id)
    start = date.today().replace(day=1)
    end = date.today()
    workflow_runs, completed = (
        await session.execute(
            text(
                "select count(*) total,count(*) filter(where status='completed') completed from workflow_runs where clinic_id=:clinic and created_at>=:start"
            ),
            {"clinic": clinic, "start": start},
        )
    ).one()
    communications = (
        await session.execute(
            text("select count(*) from communications where clinic_id=:clinic and created_at>=:start"),
            {"clinic": clinic, "start": start},
        )
    ).scalar() or 0
    minutes = float(completed) * 8.0
    value = minutes * 0.50
    methodology = {"minutes_per_completed_workflow": 8, "value_per_minute": 0.50, "currency": "USD", "note": "illustrative operational estimate; not realized revenue"}
    row = (
        await session.execute(
            text(
                """
                insert into roi_snapshots(clinic_id,period_start,period_end,workflow_runs,completed_workflows,communications,estimated_minutes_saved,estimated_value,methodology)
                values(:clinic,:start,:end,:runs,:completed,:communications,:minutes,:value,cast(:methodology as jsonb))
                returning id,period_start,period_end,workflow_runs,completed_workflows,communications,estimated_minutes_saved,estimated_value
                """
            ),
            {"clinic": clinic, "start": start, "end": end, "runs": workflow_runs, "completed": completed, "communications": communications, "minutes": minutes, "value": value, "methodology": json.dumps(methodology)},
        )
    ).mappings().one()
    return dict(row)


async def export_manifest(session, organization_id: str, actor: str, export_type: str = "operational") -> dict:
    if export_type not in {"operational", "compliance", "recovery"}:
        raise ValueError("invalid export type")
    clinic = await _clinic_id(session, organization_id)
    tables = {
        "patients": "select count(*) from patients where clinic_id=:clinic",
        "appointments": "select count(*) from appointments where clinic_id=:clinic",
        "workflows": "select count(*) from workflows where clinic_id=:clinic",
        "workflow_runs": "select count(*) from workflow_runs where clinic_id=:clinic",
        "audit_log": "select count(*) from audit_log where clinic_id=:clinic",
        "integrations": "select count(*) from integrations where clinic_id=:clinic",
    }
    counts = {}
    for name, query in tables.items():
        counts[name] = int((await session.execute(text(query), {"clinic": clinic})).scalar() or 0)
    canonical = json.dumps(counts, sort_keys=True, separators=(",", ":"))
    checksum = hashlib.sha256(canonical.encode()).hexdigest()
    row = (
        await session.execute(
            text(
                """
                insert into tenant_export_manifests(clinic_id,export_type,status,record_counts,checksum,created_by,expires_at)
                values(:clinic,:type,'ready',cast(:counts as jsonb),:checksum,:actor,now()+interval '24 hours')
                returning id,export_type,status,record_counts,checksum,created_by,expires_at,created_at
                """
            ),
            {"clinic": clinic, "type": export_type, "counts": canonical, "checksum": checksum, "actor": actor},
        )
    ).mappings().one()
    return dict(row)
