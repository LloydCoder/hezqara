"use client";
import { useState } from "react";
import { useAgents } from "@/hooks/useAgents";
import { AGENT_DESCRIPTIONS, AGENT_LABELS, type AgentType, type AgentStatus, agentStatusColor } from "@/types/agent";

function normalizeStatus(value: string): AgentStatus {
  const allowed: AgentStatus[] = ["active", "idle", "processing", "error", "disabled", "busy"];
  return allowed.includes(value as AgentStatus) ? (value as AgentStatus) : "idle";
}

export default function AgentsPage(){
 const {agents,loading,error}=useAgents(); const [selected,setSelected]=useState<AgentType|string|null>(null);
 return <main className="min-h-screen bg-slate-950 p-6 text-white"><header className="mb-6"><h1 className="text-2xl font-bold">AI Workforce</h1><p className="mt-1 text-sm text-slate-400">Organization-scoped AI workforce inventory.</p></header>
 {error&&<div className="mb-4 rounded-xl border border-red-500/20 bg-red-500/10 p-3 text-sm text-red-300">{error}</div>}
 <div className="grid gap-4 lg:grid-cols-[1fr_360px]"><section className="grid gap-3 sm:grid-cols-2">{loading?Array.from({length:10},(_,i)=><div key={i} className="h-32 animate-pulse rounded-2xl border border-white/5 bg-white/5"/>):agents.map(agent=>{const status=normalizeStatus(agent.status);const color=agentStatusColor(status);const id=agent.id as AgentType;return <article key={agent.id} className={`rounded-2xl border p-4 ${selected===agent.id?"border-white/20 bg-white/10":"border-white/5 bg-white/[0.03]"}`}><button className="w-full text-left" onClick={()=>setSelected(agent.id)}><div className="flex items-center gap-3"><span className="h-3 w-3 rounded-full" style={{background:color}}/><div><h2 className="font-semibold">{AGENT_LABELS[id] ?? agent.name}</h2><p className="text-xs capitalize text-slate-400">{status}</p></div></div></button><p className="mt-4 text-xs leading-5 text-slate-400">{AGENT_DESCRIPTIONS[id] ?? "Organization-scoped healthcare operations agent."}</p></article>})}</section>
 <aside className="rounded-2xl border border-white/5 bg-white/[0.03] p-5 lg:sticky lg:top-6 lg:self-start">{selected?<><h2 className="text-lg font-semibold">{AGENT_LABELS[selected as AgentType] ?? selected}</h2><p className="mt-2 text-sm leading-6 text-slate-400">{AGENT_DESCRIPTIONS[selected as AgentType] ?? "Agent execution is authorized and audited by the backend."}</p></>:<div className="py-12 text-center text-sm text-slate-500">Select an agent to inspect its operational role.</div>}</aside></div></main>;
}
