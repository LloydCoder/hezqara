from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.domains.patients.schemas import PatientCreate,PatientUpdate
_COLUMNS='id,first_name,last_name,date_of_birth,phone,email,insurance_carrier,insurance_member_id,created_at,updated_at'
class PatientRepository:
    def __init__(self,session:AsyncSession): self.session=session
    async def list(self,limit:int,offset:int,search:str=''):
        result=await self.session.execute(text(f"select {_COLUMNS} from patients where (:search='' or lower(first_name||' '||last_name) like lower(:pattern) or coalesce(phone,'') like :pattern) order by created_at desc,id desc limit :limit offset :offset"),{'limit':limit,'offset':offset,'search':search,'pattern':f'%{search}%'})
        return [dict(row._mapping) for row in result]
    async def get(self,patient_id:str):
        result=await self.session.execute(text(f'select {_COLUMNS} from patients where id=:id'),{'id':patient_id}); row=result.mappings().first(); return dict(row) if row else None
    async def create(self,data:PatientCreate):
        result=await self.session.execute(text(f"""insert into patients (clinic_id,first_name,last_name,date_of_birth,phone,email,insurance_carrier,insurance_member_id)
          select c.id,:first_name,:last_name,:dob,:phone,:email,:carrier,:member from clinics c where c.clerk_org_id=current_setting('app.clerk_org_id',true) returning {_COLUMNS}"""),{'first_name':data.first_name,'last_name':data.last_name,'dob':data.date_of_birth,'phone':data.phone,'email':data.email,'carrier':data.insurance_carrier,'member':data.insurance_member_id})
        row=result.mappings().first()
        if not row:raise ValueError('organization clinic is not provisioned')
        return dict(row)
    async def update(self,patient_id:str,data:PatientUpdate):
        if not data.model_dump(exclude_unset=True): return await self.get(patient_id)
        values=data.model_dump(exclude_unset=True); params={'id':patient_id,'first_name':values.get('first_name'),'last_name':values.get('last_name'),'date_of_birth':values.get('date_of_birth'),'phone':values.get('phone'),'email':values.get('email'),'insurance_carrier':values.get('insurance_carrier'),'insurance_member_id':values.get('insurance_member_id')}
        result=await self.session.execute(text(f"""update patients set first_name=coalesce(:first_name,first_name),last_name=coalesce(:last_name,last_name),date_of_birth=coalesce(:date_of_birth,date_of_birth),phone=coalesce(:phone,phone),email=coalesce(:email,email),insurance_carrier=coalesce(:insurance_carrier,insurance_carrier),insurance_member_id=coalesce(:insurance_member_id,insurance_member_id),updated_at=now() where id=:id returning {_COLUMNS}"""),params)
        row=result.mappings().first(); return dict(row) if row else None
