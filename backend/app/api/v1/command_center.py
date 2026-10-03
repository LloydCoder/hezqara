from fastapi import APIRouter,Depends
from sqlalchemy import text
from app.infrastructure.database import tenant_session_context
from app.security.authorization import require_permission
from app.security.tenant import TenantContext
router=APIRouter(prefix='/command-center',tags=['command-center'])
@router.get('/summary')
async def summary(tenant:TenantContext=Depends(require_permission('analytics:read'))):
 async with tenant_session_context(tenant.organization_id) as s:
  clinic=(await s.execute(text("SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)"))).scalar_one_or_none()
  if not clinic:return {'clinic_id':None,'queues':{},'attention':[]}
  queries={
   'appointments':"SELECT count(*) FROM appointments WHERE clinic_id=:clinic AND status IN ('scheduled','confirmed')",
   'open_care_gaps':"SELECT count(*) FROM care_gaps WHERE clinic_id=:clinic AND status IN ('open','in_progress')",
   'open_outreach':"SELECT count(*) FROM outreach_proposals WHERE clinic_id=:clinic AND status IN ('proposed','approved','queued')",
   'open_workflows':"SELECT count(*) FROM workflow_runs WHERE clinic_id=:clinic AND status IN ('queued','running','waiting_approval')",
   'open_workforce_runs':"SELECT count(*) FROM workforce_runs WHERE clinic_id=:clinic AND status IN ('queued','running','waiting_approval')",
   'open_ai_approvals':"SELECT count(*) FROM ai_approvals WHERE clinic_id=:clinic AND decision='pending'",
  }
  out={k:int((await s.execute(text(q),{'clinic':clinic})).scalar_one()) for k,q in queries.items()}
  attention=[]
  if out['open_ai_approvals']:attention.append({'queue':'ai_approvals','count':out['open_ai_approvals'],'priority':'high'})
  if out['open_workforce_runs']:attention.append({'queue':'workforce','count':out['open_workforce_runs'],'priority':'high'})
  if out['open_care_gaps']:attention.append({'queue':'care_gaps','count':out['open_care_gaps'],'priority':'normal'})
  return {'clinic_id':clinic,'queues':out,'attention':attention}
