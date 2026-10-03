import json
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy import text
from app.infrastructure.database import tenant_session_context
from app.security.authorization import require_permission
from app.security.tenant import TenantContext
from app.security.audit import append_event
from app.domains.documentation_intelligence.service import analyze_note, extract_follow_up, build_quality_summary

router = APIRouter(prefix="/documentation", tags=["documentation-intelligence"])

class AnalyzeRequest(BaseModel):
    note_text: str = Field(min_length=1)
    source_type: str = "clinical_note"
    source_ref: str | None = None
    model_version: str = "deterministic-e16.v1"

class InsightReview(BaseModel):
    status: str

@router.post("/analyze", status_code=201)
async def analyze_documentation(
    data: AnalyzeRequest,
    request: Request,
    tenant: TenantContext = Depends(require_permission("clinical_documentation:write")),
):
    if data.source_type not in {"clinical_note", "scribe_note", "record"}:
        raise HTTPException(422, "invalid documentation source type")
    findings = analyze_note(data.note_text, source_ref=data.source_ref) + extract_follow_up(data.note_text)
    summary = build_quality_summary(findings)
    async with tenant_session_context(tenant.organization_id) as s:
        check = (await s.execute(text("""
            INSERT INTO documentation_quality_checks
              (clinic_id,source_type,source_ref,score,summary,ruleset_version,model_version,status)
            VALUES (
              (SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)),
              :source_type,:source_ref,:score,:summary::jsonb,:ruleset_version,:model_version,'review'
            )
            RETURNING id,source_type,source_ref,score,summary,ruleset_version,model_version,status,created_at
        """), {
            "source_type": data.source_type,
            "source_ref": data.source_ref,
            "score": summary["score"],
            "summary": json.dumps(summary),
            "ruleset_version": "e16.v1",
            "model_version": data.model_version,
        })).mappings().one()
        for finding in findings:
            await s.execute(text("""
                INSERT INTO documentation_insights
                  (clinic_id,quality_check_id,kind,key,detail,severity,confidence,source_ref,status,provenance)
                VALUES (
                  (SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)),
                  :quality_check_id,:kind,:key,:detail,:severity,:confidence,:source_ref,'proposed',
                  :provenance::jsonb
                )
            """), {
                "quality_check_id": check["id"],
                "kind": finding.kind,
                "key": finding.key,
                "detail": finding.detail,
                "severity": finding.severity,
                "confidence": finding.confidence,
                "source_ref": finding.source_ref or data.source_ref,
                "provenance": json.dumps({"engine": "e16.deterministic", "ruleset": "e16.v1"}),
            })
        await append_event(
            s,
            organization_id=tenant.organization_id,
            actor=tenant.user_id,
            action="documentation.analyzed",
            resource_type="documentation_quality_check",
            resource_id=check["id"],
            outcome="review",
            request_id=getattr(request.state, "request_id", None),
            metadata=summary,
        )
        return dict(check) | {"findings": [f.__dict__ for f in findings]}

@router.get("/checks")
async def list_checks(
    status: str | None = None,
    limit: int = Query(50, ge=1, le=100),
    tenant: TenantContext = Depends(require_permission("clinical_documentation:read")),
):
    async with tenant_session_context(tenant.organization_id) as s:
        rows = await s.execute(text("""
            SELECT id,source_type,source_ref,score,summary,ruleset_version,model_version,status,created_at
            FROM documentation_quality_checks
            WHERE clinic_id=(SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true))
              AND (:status IS NULL OR status=:status)
            ORDER BY created_at DESC LIMIT :limit
        """), {"status": status, "limit": limit})
        return [dict(row) for row in rows.mappings()]

@router.get("/checks/{check_id}/insights")
async def list_insights(
    check_id: str,
    tenant: TenantContext = Depends(require_permission("clinical_documentation:read")),
):
    async with tenant_session_context(tenant.organization_id) as s:
        rows = await s.execute(text("""
            SELECT i.id,i.kind,i.key,i.detail,i.severity,i.confidence,i.source_ref,i.status,i.provenance,i.created_at
            FROM documentation_insights i
            JOIN documentation_quality_checks q ON q.id=i.quality_check_id AND q.clinic_id=i.clinic_id
            WHERE i.clinic_id=(SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true))
              AND q.id=:check_id
            ORDER BY i.created_at
        """), {"check_id": check_id})
        return [dict(row) for row in rows.mappings()]

@router.post("/insights/{insight_id}/review")
async def review_insight(
    insight_id: str,
    data: InsightReview,
    request: Request,
    tenant: TenantContext = Depends(require_permission("clinical_documentation:write")),
):
    if data.status not in {"accepted", "dismissed"}:
        raise HTTPException(422, "status must be accepted or dismissed")
    async with tenant_session_context(tenant.organization_id) as s:
        row = (await s.execute(text("""
            UPDATE documentation_insights
            SET status=:status, reviewed_by=:reviewer, reviewed_at=NOW()
            WHERE clinic_id=(SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true))
              AND id=:id AND status='proposed'
            RETURNING id,status,reviewed_by,reviewed_at
        """), {"id": insight_id, "status": data.status, "reviewer": tenant.user_id})).mappings().first()
        if not row:
            raise HTTPException(404, "proposed insight not found")
        await append_event(
            s, organization_id=tenant.organization_id, actor=tenant.user_id,
            action="documentation.insight_reviewed", resource_type="documentation_insight",
            resource_id=insight_id, outcome=data.status,
            request_id=getattr(request.state, "request_id", None),
        )
        return dict(row)
