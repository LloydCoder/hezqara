"use client";

import { useState } from "react";
import { useAgents } from "@/hooks/useAgents";
import {
  AGENT_DESCRIPTIONS,
  AGENT_LABELS,
  type AgentType,
  agentStatusColor,
} from "@/types/agent";

const CLINIC_ID = process.env.NEXT_PUBLIC_DEMO_CLINIC_ID ?? "demo_clinic";

export default function AgentsPage() {
  const { agents, loading, error, toggleAgent } = useAgents(CLINIC_ID);
  const [selected, setSelected] = useState<AgentType | null>(null);

  return (
    <main className="min-h-screen bg-slate-950 p-6 text-white">
      <header className="mb-6">
        <h1 className="text-2xl font-bold">AI Workforce</h1>
        <p className="mt-1 text-sm text-slate-400">Monitor and control your healthcare operations agents.</p>
      </header>

      {error && (
        <div className="mb-4 rounded-xl border border-red-500/20 bg-red-500/10 p-3 text-sm text-red-300">
          {error}
        </div>
      )}

      <div className="grid gap-4 lg:grid-cols-[1fr_360px]">
        <section className="grid gap-3 sm:grid-cols-2">
          {loading
            ? Array.from({ length: 10 }, (_, index) => (
                <div key={index} className="h-32 animate-pulse rounded-2xl border border-white/5 bg-white/5" />
              ))
            : agents.map((agent) => {
                const color = agentStatusColor(agent.status);
                const enabled = agent.status !== "disabled";
                return (
                  <article
                    key={agent.id}
                    className={`rounded-2xl border p-4 transition ${selected === agent.id ? "border-white/20 bg-white/10" : "border-white/5 bg-white/[0.03]"}`}
                  >
                    <div className="flex items-start justify-between gap-3">
                      <button className="min-w-0 text-left" onClick={() => setSelected(agent.id)}>
                        <div className="flex items-center gap-3">
                          <span className="h-3 w-3 shrink-0 rounded-full" style={{ background: color }} />
                          <div>
                            <h2 className="font-semibold">{AGENT_LABELS[agent.id]}</h2>
                            <p className="text-xs capitalize text-slate-400">{agent.status}</p>
                          </div>
                        </div>
                      </button>
                      <button
                        type="button"
                        aria-label={`${enabled ? "Disable" : "Enable"} ${AGENT_LABELS[agent.id]} agent`}
                        aria-pressed={enabled}
                        onClick={() => toggleAgent?.(agent.id, !enabled)}
                        className="h-6 w-11 rounded-full border border-white/10 p-0.5"
                      >
                        <span
                          className="block h-4 w-4 rounded-full transition-transform"
                          style={{
                            background: color,
                            transform: enabled ? "translateX(20px)" : "translateX(0)",
                          }}
                        />
                      </button>
                    </div>
                    <p className="mt-4 text-xs leading-5 text-slate-400">{agent.description || AGENT_DESCRIPTIONS[agent.id]}</p>
                    <dl className="mt-4 grid grid-cols-3 gap-2 text-xs">
                      <div><dt className="text-slate-500">Calls</dt><dd className="mt-1 font-semibold">{agent.calls_handled_today}</dd></div>
                      <div><dt className="text-slate-500">Success</dt><dd className="mt-1 font-semibold">{Math.round(agent.success_rate * 100)}%</dd></div>
                      <div><dt className="text-slate-500">Avg.</dt><dd className="mt-1 font-semibold">{Math.round(agent.avg_handle_time_seconds / 60)}m</dd></div>
                    </dl>
                  </article>
                );
              })}
        </section>

        <aside className="rounded-2xl border border-white/5 bg-white/[0.03] p-5 lg:sticky lg:top-6 lg:self-start">
          {selected ? (
            <>
              <h2 className="text-lg font-semibold">{AGENT_LABELS[selected]}</h2>
              <p className="mt-2 text-sm leading-6 text-slate-400">{AGENT_DESCRIPTIONS[selected]}</p>
              <div className="mt-6 rounded-xl bg-white/5 p-4 text-sm text-slate-300">
                Operational metrics shown here are sourced from the API. No synthetic activity is generated in the dashboard.
              </div>
            </>
          ) : (
            <div className="py-12 text-center text-sm text-slate-500">Select an agent to inspect its operational state.</div>
          )}
        </aside>
      </div>
    </main>
  );
}
