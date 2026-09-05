import subprocess,sys,time
import httpx
BASE='http://127.0.0.1:8004'
def call(client,method,path,**kwargs):
    response=client.request(method,path,timeout=10,headers={'x-test-auth':'1',**kwargs.pop('headers',{})},**kwargs)
    print(f'{method} {path} -> {response.status_code} {response.text}',flush=True); response.raise_for_status(); return response.json()
proc=subprocess.Popen([sys.executable,'-m','uvicorn','app.main:app','--host','127.0.0.1','--port','8004'],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
try:
    with httpx.Client(base_url=BASE) as client:
        for _ in range(30):
            try:
                if client.get('/health',timeout=2).is_success: break
            except httpx.HTTPError: pass
            time.sleep(1)
        call(client,'GET','/health')
        patient=call(client,'POST','/api/v1/patients',json={'first_name':'Synthetic','last_name':'Patient','email':'synthetic@example.invalid'}); patient_id=patient['id']
        call(client,'GET',f'/api/v1/patients/{patient_id}')
        call(client,'POST','/api/v1/appointments',json={'patient_id':patient_id,'appointment_datetime':'2030-01-01T10:00:00Z','duration_minutes':20,'reason':'CI test'})
        task=call(client,'POST','/api/v1/tasks',json={'title':'CI operational task','priority':'high'}); task_id=task['id']; call(client,'PATCH',f'/api/v1/tasks/{task_id}',json={'status':'in_progress'})
        workflow=call(client,'POST','/api/v1/workflows',json={'key':'appointment_operations','name':'Appointment Operations','definition':{'steps':[{'key':'create_task','type':'create_task','input':{'title':'Workflow-created operational task','priority':'normal'}},{'key':'finish','type':'complete'}]}}); workflow_id=workflow['id']
        call(client,'POST',f'/api/v1/workflows/{workflow_id}/activate')
        run=call(client,'POST',f'/api/v1/workflows/{workflow_id}/runs',json={'idempotency_key':'ci-workflow-run-001','trigger_type':'manual','context':{}}); assert run['status']=='completed',run
        duplicate=call(client,'POST',f'/api/v1/workflows/{workflow_id}/runs',json={'idempotency_key':'ci-workflow-run-001','trigger_type':'manual','context':{}}); assert duplicate['id']==run['id']
        call(client,'GET','/api/v1/workflows'); call(client,'GET',f'/api/v1/workflows/{workflow_id}/runs'); call(client,'GET','/api/v1/audit'); call(client,'GET','/api/v1/operations/summary')
finally:
    proc.terminate()
    try: proc.wait(timeout=5)
    except subprocess.TimeoutExpired: proc.kill()
    output=proc.stdout.read() if proc.stdout else ''
    if output: print(output,flush=True)
