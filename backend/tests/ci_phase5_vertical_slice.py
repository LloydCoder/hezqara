import asyncio,subprocess,sys,time
import httpx
BASE='http://127.0.0.1:8004'
def call(client,method,path,**kwargs):
 r=client.request(method,path,timeout=10,headers={'x-test-auth':'1',**kwargs.pop('headers',{})},**kwargs); print(f'{method} {path} -> {r.status_code} {r.text}',flush=True); r.raise_for_status(); return r.json()
proc=subprocess.Popen([sys.executable,'-m','uvicorn','app.main:app','--host','127.0.0.1','--port','8004'],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
try:
 with httpx.Client(base_url=BASE) as client:
  for _ in range(30):
   try:
    if client.get('/health',timeout=2).is_success: break
   except httpx.HTTPError: pass
   time.sleep(1)
  patient=call(client,'POST','/api/v1/patients',json={'first_name':'Phase5','last_name':'Patient','email':'phase5@example.invalid','phone':'15550001111'}); pid=patient['id']
  appt=call(client,'POST','/api/v1/appointments',json={'patient_id':pid,'appointment_datetime':'2031-01-01T10:00:00Z','duration_minutes':30,'reason':'Phase 5','provider_id':'provider-1'}); aid=appt['id']
  conflict=client.post('/api/v1/appointments',json={'patient_id':pid,'appointment_datetime':'2031-01-01T10:15:00Z','duration_minutes':20,'provider_id':'provider-1'},headers={'x-test-auth':'1'}); assert conflict.status_code==409,conflict.text
  call(client,'PUT',f'/api/v1/communications/patients/{pid}/preferences',json={'sms_enabled':True,'email_enabled':True,'whatsapp_enabled':False,'opted_out_all':False,'timezone':'UTC'})
  communication=call(client,'POST','/api/v1/communications',json={'patient_id':pid,'appointment_id':aid,'channel':'email','body':'Your appointment is confirmed.','idempotency_key':'phase5-communication-001'}); assert communication['status']=='queued'
  asyncio.run(__import__('app.domains.patient_engagement.outbox',fromlist=['process_communication_outbox']).process_communication_outbox('test_org'))
  communications=call(client,'GET','/api/v1/communications'); sent=[x for x in communications if x['id']==communication['id']][0]; assert sent['status']=='sent',sent
  classification=call(client,'POST','/api/v1/communications/intake',json={'patient_id':pid,'channel':'email','message':'I need to reschedule my appointment'}); assert classification['intent']=='reschedule',classification
  workflow=call(client,'POST','/api/v1/workflows',json={'key':'phase5_approval','name':'Phase 5 Approval Workflow','definition':{'steps':[{'key':'approval','type':'request_approval','input':{'risk_level':'EXTERNAL_SIDE_EFFECT','action':{'type':'send_patient_message'}}},{'key':'finish','type':'complete'}]}}); wid=workflow['id']; call(client,'POST',f'/api/v1/workflows/{wid}/activate')
  run=call(client,'POST',f'/api/v1/workflows/{wid}/runs',json={'idempotency_key':'phase5-workflow-001','trigger_type':'manual','context':{}}); assert run['status']=='waiting_for_approval',run
  approvals=call(client,'GET','/api/v1/approvals'); approval=next(x for x in approvals if x['workflow_run_id']==run['id']); call(client,'POST',f"/api/v1/approvals/{approval['id']}/approve"); runs=call(client,'GET',f'/api/v1/workflows/{wid}/runs'); assert runs[0]['status']=='completed',runs
  summary=call(client,'GET','/api/v1/operations/summary'); assert summary['active_workflows']>=0 and 'queued_communications' in summary
finally:
 proc.terminate()
 try: proc.wait(timeout=5)
 except subprocess.TimeoutExpired: proc.kill()
 output=proc.stdout.read() if proc.stdout else ''
 if output: print(output,flush=True)
