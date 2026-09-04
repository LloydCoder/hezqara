"use client";
import { useAgents, useAnalytics, useCalls } from "@/hooks/useAgents";
function Stat({label,value}:{label:string;value:React.ReactNode}){return <article className="rounded-2xl border border-white/10 bg-slate-900 p-5"><p className="text-xs uppercase tracking-wider text-white/40">{label}</p><p className="mt-2 text-3xl font-black text-white">{value}</p></article>}
export default function DashboardPage(){
 const {agents,loading:agentsLoading}=useAgents(); const {summary,loading:analyticsLoading}=useAnalytics(); const {calls,loading:callsLoading}=useCalls();
 const ready=agents.filter(a=>a.status!=="disabled").length;
 return <main className="min-h-screen space-y-6 bg-slate-950 p-6 text-white">
  <header><h1 className="text-2xl font-black">HEZQARA Command Centre</h1><p className="mt-1 text-sm text-white/50">Live clinic operations and AI workforce activity.</p></header>
  <section className="grid gap-4 md:grid-cols-4"><Stat label="Calls handled" value={analyticsLoading?"…":summary?.total_calls??"Unavailable"}/><Stat label="Appointments booked" value={analyticsLoading?"…":summary?.total_appointments_booked??"Unavailable"}/><Stat label="Available agents" value={agentsLoading?"…":ready}/><Stat label="Recent calls" value={callsLoading?"…":calls.length}/></section>
  {!analyticsLoading&&!summary&&<p className="rounded-xl border border-white/10 p-4 text-sm text-white/50">Analytics data is unavailable. No synthetic metrics are shown.</p>}
  <section className="rounded-2xl border border-white/10 bg-slate-900 p-5"><h2 className="font-bold">AI workforce</h2><div className="mt-4 grid gap-2 sm:grid-cols-2 lg:grid-cols-5">{agents.map(agent=><div key={agent.id} className="rounded-xl border border-white/10 p-3"><p className="font-medium">{agent.name}</p><p className="text-xs text-white/50">{agent.status}</p></div>)}</div>{!agentsLoading&&agents.length===0&&<p className="mt-3 text-sm text-white/50">No agents are available for this organization.</p>}</section>
 </main>;
}
