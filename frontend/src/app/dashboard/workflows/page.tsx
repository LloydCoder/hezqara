'use client';

import { useCallback, useEffect, useState } from 'react';
import api, { APIError, Workflow } from '@/lib/api';

export default function WorkflowsPage() {
  const [workflows,setWorkflows]=useState<Workflow[]>([]);
  const [loading,setLoading]=useState(true);
  const [error,setError]=useState<string|null>(null);
  const [busy,setBusy]=useState<string|null>(null);

  const load=useCallback(async()=>{setLoading(true);setError(null);try{setWorkflows(await api.workflows.list())}catch(err){setError(err instanceof APIError?err.message:'Unable to load workflows')}finally{setLoading(false)}},[]);
  useEffect(()=>{void load()},[load]);

  async function activate(id:string){setBusy(id);setError(null);try{await api.workflows.activate(id);await load()}catch(err){setError(err instanceof APIError?err.message:'Unable to activate workflow')}finally{setBusy(null)}}
  async function run(id:string){setBusy(id);setError(null);try{await api.workflows.run(id,{idempotency_key:`ui-${id}-${Date.now()}`,trigger_type:'manual',context:{}});await load()}catch(err){setError(err instanceof APIError?err.message:'Unable to execute workflow')}finally{setBusy(null)}}

  return <main className="space-y-6 p-6" aria-labelledby="workflows-heading">
    <header><h1 id="workflows-heading" className="text-2xl font-semibold">Workflows</h1><p className="text-sm text-muted-foreground">Authoritative workflow definitions and execution controls.</p></header>
    {error&&<div role="alert" className="rounded-md border p-3 text-sm">{error}</div>}
    {loading?<p role="status">Loading workflows…</p>:workflows.length===0?<section className="rounded-lg border p-6"><h2 className="font-medium">No workflows configured</h2><p className="mt-1 text-sm text-muted-foreground">Create a workflow through the authorized API before it can be activated or executed.</p></section>:<div className="overflow-x-auto rounded-lg border"><table className="w-full text-left text-sm"><caption className="sr-only">Configured workflows</caption><thead><tr className="border-b"><th scope="col" className="p-3">Name</th><th scope="col" className="p-3">Version key</th><th scope="col" className="p-3">Status</th><th scope="col" className="p-3">Actions</th></tr></thead><tbody>{workflows.map(w=><tr key={w.id} className="border-b last:border-0"><td className="p-3 font-medium">{w.name}</td><td className="p-3 font-mono text-xs">{w.key}</td><td className="p-3"><span aria-label={`Status ${w.status}`}>{w.status}</span></td><td className="p-3"><div className="flex flex-wrap gap-2">{w.status==='draft'&&<button type="button" className="rounded-md border px-3 py-1.5" disabled={busy===w.id} onClick={()=>void activate(w.id)}>{busy===w.id?'Working…':'Activate'}</button>}{w.status==='active'&&<button type="button" className="rounded-md border px-3 py-1.5" disabled={busy===w.id} onClick={()=>void run(w.id)}>{busy===w.id?'Running…':'Run'}</button>}</div></td></tr>)}</tbody></table></div>}
  </main>;
}
