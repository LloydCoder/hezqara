"use client";
import { useState } from "react";
import { useAgents } from "@/hooks/useAgents";
import { AGENT_DESCRIPTIONS, AGENT_LABELS, type AgentReadiness, type AgentType } from "@/types/agent";
import { AgentIdentity, AgentStatus } from "@/components/ui/ai";
import { Card, EmptyState, ErrorState, Skeleton } from "@/components/ui/primitives";
import { ContentContainer, PageHeader, PageSection } from "@/components/ui/layout";

function readinessFromApi(value: string): AgentReadiness { if (value === "ready" || value === "available") return "ready"; if (value === "disabled") return "disabled"; if (value === "not_configured") return "not_configured"; return "unavailable"; }

export default function AgentsPage() {
  const { agents, loading, error, reload } = useAgents();
  const [selected, setSelected] = useState<string | null>(null);
  const selectedAgent = agents.find(agent => agent.id === selected);
  return <main className="hz-page"><ContentContainer><PageSection><PageHeader eyebrow="Workforce" title="AI Workforce" description="Organization-scoped workforce inventory. Availability is intentionally separated from runtime execution." /><div className="mt-6 grid gap-5 lg:grid-cols-[minmax(0,1fr)_360px]">{error ? <ErrorState description={error} onRetry={reload} /> : loading ? <div className="grid gap-3 sm:grid-cols-2">{Array.from({length: 10}, (_, i) => <Skeleton key={i} className="h-32" />)}</div> : agents.length === 0 ? <EmptyState title="No workforce data available" description="No organization-scoped agent records were returned." /> : <section aria-label="AI workforce agents" className="grid gap-3 sm:grid-cols-2">{agents.map(agent => { const id = agent.id as AgentType; const readiness = readinessFromApi(agent.status); return <button key={agent.id} type="button" onClick={() => setSelected(agent.id)} aria-pressed={selected === agent.id} className={`rounded-xl border p-5 text-left transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-700 ${selected === agent.id ? "border-slate-700 bg-slate-50" : "border-slate-200 bg-white hover:border-slate-300"}`}><div className="flex items-start justify-between gap-3"><AgentIdentity name={AGENT_LABELS[id] ?? agent.name} purpose={agent.description ?? AGENT_DESCRIPTIONS[id]} /><AgentStatus state={readiness} /></div></button>; })}</section>}
          <aside className="rounded-xl border border-slate-200 bg-white p-5 lg:sticky lg:top-6 lg:self-start" aria-label="Agent details">{selectedAgent ? <><AgentIdentity name={AGENT_LABELS[selectedAgent.id as AgentType] ?? selectedAgent.name} purpose={selectedAgent.description ?? AGENT_DESCRIPTIONS[selectedAgent.id as AgentType]} /><div className="mt-5"><AgentStatus state={readinessFromApi(selectedAgent.status)} /></div><p className="mt-5 text-sm leading-6 text-slate-600">This inventory record does not establish that an agent is currently running. Execution state will be shown only from an execution record.</p></> : <p className="py-10 text-center text-sm leading-6 text-slate-500">Select an agent to inspect its role and readiness.</p>}</aside></div></PageSection></ContentContainer></main>;
}
