from sqlalchemy import text
from app.domains.patient_engagement.providers import build_communication_provider
from app.infrastructure.database import tenant_session_context
async def process_communication_outbox(organization_id:str,limit:int=20)->int:
    processed=0
    async with tenant_session_context(organization_id) as session:
        clinic=(await session.execute(text('select id from clinics where clerk_org_id=:org'),{'org':organization_id})).scalar_one_or_none()
        if not clinic:return 0
        for _ in range(limit):
            row=(await session.execute(text("select id,aggregate_id from outbox_events where clinic_id=:clinic and event_type='communication.dispatch' and status='pending' and available_at<=now() order by created_at,id for update skip locked limit 1"),{'clinic':clinic})).mappings().first()
            if not row:break
            await session.execute(text("update outbox_events set status='processing',attempts=attempts+1,updated_at=now() where id=:id"),{'id':row['id']})
            comm=(await session.execute(text('select c.*,p.phone,p.email from communications c join patients p on p.id=c.patient_id where c.id=:id and c.clinic_id=:clinic for update'),{'id':row['aggregate_id'],'clinic':clinic})).mappings().first()
            if not comm:
                await session.execute(text("update outbox_events set status='failed',last_error='communication_not_found',updated_at=now() where id=:id"),{'id':row['id']}); continue
            try:
                provider=build_communication_provider(); reference,status=await provider.send(channel=comm['channel'],patient=dict(comm),body=comm['body'],subject=comm['subject'])
                await session.execute(text("update communications set status=:status,provider_reference=:reference,sent_at=case when :status in ('sent','delivered') then now() else sent_at end,updated_at=now() where id=:id"),{'status':status,'reference':reference,'id':comm['id']})
                await session.execute(text("insert into communication_events(clinic_id,communication_id,event_type,provider_reference) values(:clinic,:comm,'communication.sent',:reference)"),{'clinic':clinic,'comm':comm['id'],'reference':reference})
                await session.execute(text("update outbox_events set status='published',updated_at=now() where id=:id"),{'id':row['id']}); processed+=1
            except Exception as exc:
                await session.execute(text("update communications set status='failed',failure_class=:failure,updated_at=now() where id=:id"),{'failure':type(exc).__name__,'id':comm['id']})
                await session.execute(text("update outbox_events set status=case when attempts>=5 then 'failed' else 'pending' end,last_error=:error,available_at=now()+interval '5 minutes',updated_at=now() where id=:id"),{'error':type(exc).__name__,'id':row['id']})
    return processed
