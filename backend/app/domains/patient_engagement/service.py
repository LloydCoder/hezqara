from __future__ import annotations
import uuid
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.domains.patient_engagement.schemas import CommunicationCreate,CommunicationPreferenceUpdate
class CommunicationProvider:
    name='unavailable'
    async def send(self,*,channel:str,patient:dict,body:str,subject:str|None=None)->tuple[str,str]: raise RuntimeError('communication provider is not configured')
class DeterministicTestProvider(CommunicationProvider):
    name='deterministic-test'
    async def send(self,*,channel:str,patient:dict,body:str,subject:str|None=None)->tuple[str,str]: return f'test-{uuid.uuid4()}','sent'
class WhatsAppCloudProvider(CommunicationProvider):
    name='whatsapp-cloud'
    def __init__(self,token:str,phone_number_id:str): self.token=token; self.phone_number_id=phone_number_id
    async def send(self,*,channel:str,patient:dict,body:str,subject:str|None=None)->tuple[str,str]:
        import httpx
        phone=patient.get('phone')
        if not phone: raise ValueError('patient phone is required for WhatsApp')
        url=f'https://graph.facebook.com/v23.0/{self.phone_number_id}/messages'; payload={'messaging_product':'whatsapp','to':phone,'type':'text','text':{'body':body}}
        async with httpx.AsyncClient(timeout=20) as client:
            response=await client.post(url,json=payload,headers={'Authorization':f'Bearer {self.token}'})
            response.raise_for_status(); data=response.json()
        messages=data.get('messages') or []
        if not messages or not messages[0].get('id'): raise RuntimeError('WhatsApp provider returned no message id')
        return str(messages[0]['id']),'sent'
class CommunicationService:
    def __init__(self,session:AsyncSession,provider:CommunicationProvider): self.session=session; self.provider=provider
    async def clinic_id(self,organization_id:str)->str:
        row=(await self.session.execute(text('select id from clinics where clerk_org_id=:org'),{'org':organization_id})).scalar_one_or_none()
        if not row: raise ValueError('organization clinic not found')
        return str(row)
    async def _patient(self,clinic_id:str,patient_id:str)->dict:
        row=(await self.session.execute(text('select id,first_name,last_name,phone,email from patients where id=:id and clinic_id=:clinic'),{'id':patient_id,'clinic':clinic_id})).mappings().first()
        if not row: raise ValueError('patient not found')
        return dict(row)
    async def _allowed(self,clinic_id:str,patient_id:str,channel:str)->bool:
        row=(await self.session.execute(text('select sms_enabled,email_enabled,whatsapp_enabled,opted_out_all from patient_communication_preferences where clinic_id=:clinic and patient_id=:patient'),{'clinic':clinic_id,'patient':patient_id})).mappings().first()
        if not row:return channel in {'sms','email'}
        if row['opted_out_all']:return False
        return bool({'sms':row['sms_enabled'],'email':row['email_enabled'],'whatsapp':row['whatsapp_enabled']}[channel])
    async def queue(self,organization_id:str,data:CommunicationCreate,correlation_id:str|None=None)->dict:
        clinic=await self.clinic_id(organization_id); await self._patient(clinic,data.patient_id)
        existing=(await self.session.execute(text('select * from communications where clinic_id=:clinic and idempotency_key=:key'),{'clinic':clinic,'key':data.idempotency_key})).mappings().first()
        if existing:return dict(existing)
        status='queued' if await self._allowed(clinic,data.patient_id,data.channel) else 'blocked'
        row=(await self.session.execute(text("insert into communications(clinic_id,patient_id,appointment_id,workflow_run_id,channel,direction,status,subject,body,template_key,idempotency_key,correlation_id) values(:clinic,:patient,:appointment,:run,:channel,'outbound',:status,:subject,:body,:template,:key,:correlation) returning *"),{'clinic':clinic,'patient':data.patient_id,'appointment':data.appointment_id,'run':data.workflow_run_id,'channel':data.channel,'status':status,'subject':data.subject,'body':data.body,'template':data.template_key,'key':data.idempotency_key,'correlation':correlation_id})).mappings().first()
        if status=='queued':
            await self.session.execute(text("insert into outbox_events(clinic_id,event_type,aggregate_type,aggregate_id,payload,idempotency_key) values(:clinic,'communication.dispatch','communication',:comm,cast(:payload as jsonb),:key) on conflict (clinic_id,idempotency_key) do nothing"),{'clinic':clinic,'comm':row['id'],'payload':'{}','key':f'communication:{row["id"]}'})
        return dict(row)
    async def preferences(self,organization_id:str,patient_id:str,data:CommunicationPreferenceUpdate)->dict:
        clinic=await self.clinic_id(organization_id); await self._patient(clinic,patient_id)
        await self.session.execute(text("insert into patient_communication_preferences(clinic_id,patient_id,sms_enabled,email_enabled,whatsapp_enabled,opted_out_all,timezone) values(:clinic,:patient,:sms,:email,:whatsapp,:opted,:timezone) on conflict (clinic_id,patient_id) do update set sms_enabled=excluded.sms_enabled,email_enabled=excluded.email_enabled,whatsapp_enabled=excluded.whatsapp_enabled,opted_out_all=excluded.opted_out_all,timezone=excluded.timezone,updated_at=now()"),{'clinic':clinic,'patient':patient_id,'sms':data.sms_enabled,'email':data.email_enabled,'whatsapp':data.whatsapp_enabled,'opted':data.opted_out_all,'timezone':data.timezone})
        return dict((await self.session.execute(text('select patient_id,sms_enabled,email_enabled,whatsapp_enabled,opted_out_all,timezone,updated_at from patient_communication_preferences where clinic_id=:clinic and patient_id=:patient'),{'clinic':clinic,'patient':patient_id})).mappings().first())
