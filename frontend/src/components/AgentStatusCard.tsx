"use client";
import { AGENT_DESCRIPTIONS, AGENT_LABELS, type Agent } from "@/types/agent";
import { StatusBadge } from "@/components/ui/primitives";
import { readinessTone, READINESS_LABELS } from "@/types/ui";

export function AgentStatusCard({ agent, onToggle }: { agent: Agent; onToggle?: (enabled: boolean) => void }) {
  return <article className="flex flex-col gap-4 rounded-xl border border-slate-200 bg-white p-5"><div className="flex items-start justify-between gap-4"><div><p className="text-sm font-semibold text-slate-900">{AGENT_LABELS[agent.id]}</p><p className="mt-1 text-xs leading-5 text-slate-600">{agent.description ?? AGENT_DESCRIPTIONS[agent.id]}</p></div>{onToggle ? <button type="button" onClick={() => onToggle(agent.readiness !== "ready")} aria-label={`Toggle ${AGENT_LABELS[agent.id]}`} className="min-h-11 min-w-11 rounded-lg border border-slate-200 px-3 text-xs font-semibold hover:bg-slate-50">{agent.readiness === "ready" ? "On" : "Off"}</button> : null}</div><StatusBadge tone={readinessTone(agent.readiness)} label={READINESS_LABELS[agent.readiness]} /><p className="border-t border-slate-100 pt-3 text-xs leading-5 text-slate-500">Readiness describes availability only; it is not a runtime execution state.</p></article>;
}
