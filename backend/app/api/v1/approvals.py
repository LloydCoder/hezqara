from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text
from app.infrastructure.database import tenant_session_context
from app.security.authorization import require_permission
from app.security.tenant import TenantContext
from app.security.audit import append_event

router = APIRouter(prefix='/approvals', tags=['approvals'])

class DecisionRequest(BaseModel):
    reason: str | None = Field(default=None, max_length=1000)

@router.get('')
async def list_approvals(tenant: TenantContext = Depends(require_permission('approvals:read'))):
    async with tenant_session_context(tenant.organization_id) as session:
        rows = (await session.execute(text(
            """select id,workflow_run_id,workflow_step_run_id,risk_level,status,
            requested_by,decided_by,expires_at,decided_at,created_at
            from workflow_approvals order by created_at desc,id desc limit 100"""
        ))).mappings()
        return [dict(row) for row in rows]

@router.get('/ai')
async def list_ai_approvals(tenant: TenantContext = Depends(require_permission('approvals:read'))):
    async with tenant_session_context(tenant.organization_id) as session:
        rows = (await session.execute(text(
            """select id,execution_id,actor_id,proposed_action,evidence,risk_tier,
            policy_version,decision,rejection_reason,decided_by,decision_reason,
            expires_at,decided_at,created_at
            from ai_approvals order by created_at desc,id desc limit 100"""
        ))).mappings()
        return [dict(row) for row in rows]

async def _decide_workflow(approval_id: str, tenant: TenantContext, status: str):
    run_id = None
    async with tenant_session_context(tenant.organization_id) as session:
        row = (await session.execute(text(
            """select id,status,expires_at,workflow_run_id,workflow_step_run_id
            from workflow_approvals
            where id=:id
              and clinic_id in (select id from clinics where clerk_org_id=current_setting('app.clerk_org_id',true))
            for update"""
        ), {'id': approval_id})).mappings().first()
        if not row:
            raise HTTPException(status_code=404, detail='approval not found')
        if row['status'] != 'pending':
            raise HTTPException(status_code=409, detail='approval is no longer pending')
        if row['expires_at'] and row['expires_at'] <= datetime.now(timezone.utc):
            await session.execute(text(
                "update workflow_approvals set status='expired' where id=:id and status='pending'"
            ), {'id': approval_id})
            raise HTTPException(status_code=409, detail='approval expired')

        updated = (await session.execute(text(
            """update workflow_approvals
            set status=:status,decided_by=:actor,decided_at=now()
            where id=:id and status='pending'
            returning id,workflow_run_id,workflow_step_run_id,risk_level,status,
                      requested_by,decided_by,expires_at,decided_at,created_at"""
        ), {'id': approval_id, 'status': status, 'actor': tenant.user_id})).mappings().first()
        if not updated:
            raise HTTPException(status_code=409, detail='approval decision race')

        run_id = updated['workflow_run_id']
        if status == 'approved':
            await session.execute(text(
                """update workflow_step_runs
                set status='queued'
                where id=:step
                  and clinic_id in (select id from clinics where clerk_org_id=current_setting('app.clerk_org_id',true))
                  and status='waiting_for_approval'"""
            ), {'step': updated['workflow_step_run_id']})
        await append_event(
            session,
            organization_id=tenant.organization_id,
            actor=tenant.user_id,
            action=f'workflow.approval.{status}',
            resource_type='workflow_approval',
            resource_id=approval_id,
            outcome=status,
            metadata={'workflow_run_id': run_id},
        )
        result = dict(updated)

    if status == 'approved' and run_id:
        from app.domains.workflows.runtime import execute_run
        result['workflow_run'] = await execute_run(tenant.organization_id, run_id)
    return result

async def _decide_ai(approval_id: str, tenant: TenantContext, status: str, reason: str | None):
    async with tenant_session_context(tenant.organization_id) as session:
        row = (await session.execute(text(
            """select id,execution_id,actor_id,proposed_action,evidence,risk_tier,
            policy_version,decision,rejection_reason,decided_by,decision_reason,
            expires_at,decided_at,created_at
            from ai_approvals
            where id=:id
              and clinic_id in (select id from clinics where clerk_org_id=current_setting('app.clerk_org_id',true))
            for update"""
        ), {'id': approval_id})).mappings().first()
        if not row:
            raise HTTPException(status_code=404, detail='AI approval not found')
        if row['decision'] != 'pending':
            raise HTTPException(status_code=409, detail='AI approval is no longer pending')
        if row['expires_at'] and row['expires_at'] <= datetime.now(timezone.utc):
            await session.execute(text(
                "update ai_approvals set decision='rejected',rejection_reason='approval expired',decided_by=:actor,decision_reason='approval expired',decided_at=now() where id=:id and decision='pending'"
            ), {'id': approval_id, 'actor': tenant.user_id})
            raise HTTPException(status_code=409, detail='AI approval expired')
        if status == 'rejected' and not reason:
            raise HTTPException(status_code=400, detail='rejection reason is required')

        updated = (await session.execute(text(
            """update ai_approvals
            set decision=:decision,
                rejection_reason=:rejection_reason,
                decided_by=:actor,
                decision_reason=:reason,
                decided_at=now()
            where id=:id and decision='pending'
            returning id,execution_id,actor_id,proposed_action,evidence,risk_tier,
                      policy_version,decision,rejection_reason,decided_by,decision_reason,
                      expires_at,decided_at,created_at"""
        ), {
            'id': approval_id,
            'decision': status,
            'rejection_reason': reason if status == 'rejected' else None,
            'actor': tenant.user_id,
            'reason': reason,
        })).mappings().first()
        if not updated:
            raise HTTPException(status_code=409, detail='AI approval decision race')

        await append_event(
            session,
            organization_id=tenant.organization_id,
            actor=tenant.user_id,
            action=f'ai.approval.{status}',
            resource_type='ai_approval',
            resource_id=approval_id,
            outcome=status,
            metadata={'execution_id': updated['execution_id'], 'risk_tier': updated['risk_tier']},
        )
        return dict(updated)

@router.post('/{approval_id}/approve')
async def approve(approval_id: str, tenant: TenantContext = Depends(require_permission('approvals:approve'))):
    return await _decide_workflow(approval_id, tenant, 'approved')

@router.post('/{approval_id}/reject')
async def reject(approval_id: str, body: DecisionRequest | None = None, tenant: TenantContext = Depends(require_permission('approvals:approve'))):
    return await _decide_workflow(approval_id, tenant, 'rejected')

@router.post('/ai/{approval_id}/approve')
async def approve_ai(approval_id: str, tenant: TenantContext = Depends(require_permission('approvals:approve'))):
    return await _decide_ai(approval_id, tenant, 'approved', None)

@router.post('/ai/{approval_id}/reject')
async def reject_ai(approval_id: str, body: DecisionRequest | None = None, tenant: TenantContext = Depends(require_permission('approvals:approve'))):
    return await _decide_ai(approval_id, tenant, 'rejected', body.reason if body else None)
