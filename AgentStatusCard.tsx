"use client";

import { agentStatusColor, AGENT_LABELS, AGENT_DESCRIPTIONS } from "@/types/agent";
import type { Agent } from "@/types/agent";
import { cn } from "@/lib/utils";

interface AgentStatusCardProps {
  agent: Agent;
  onToggle?: (enabled: boolean) => void;
}

export function AgentStatusCard({ agent, onToggle }: AgentStatusCardProps) {
  const isActive = agent.status === "active" || agent.status === "processing";

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5 flex flex-col gap-3">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm font-semibold text-slate-900">
            {AGENT_LABELS[agent.id]}
          </p>
          <p className="text-xs text-slate-500 mt-0.5">
            {AGENT_DESCRIPTIONS[agent.id]}
          </p>
        </div>

        {/* Toggle */}
        {onToggle && (
          <button
            onClick={() => onToggle(!isActive)}
            className={cn(
              "relative inline-flex h-5 w-9 items-center rounded-full transition-colors",
              isActive ? "bg-emerald-500" : "bg-slate-200"
            )}
          >
            <span
              className={cn(
                "inline-block h-3.5 w-3.5 rounded-full bg-white shadow transition-transform",
                isActive ? "translate-x-4" : "translate-x-0.5"
              )}
            />
          </button>
        )}
      </div>

      {/* Status badge */}
      <div className="flex items-center gap-2">
        <span
          className={cn(
            "inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium",
            agentStatusColor(agent.status)
          )}
        >
          {agent.status}
        </span>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-2 pt-2 border-t border-slate-100">
        <div>
          <p className="text-xs text-slate-400">Today</p>
          <p className="text-sm font-semibold text-slate-800">
            {agent.calls_handled_today}
          </p>
        </div>
        <div>
          <p className="text-xs text-slate-400">Avg time</p>
          <p className="text-sm font-semibold text-slate-800">
            {Math.round(agent.avg_handle_time_seconds / 60)}m
          </p>
        </div>
        <div>
          <p className="text-xs text-slate-400">AI cost</p>
          <p className="text-sm font-semibold text-slate-800">
            ${agent.cost_today_usd.toFixed(2)}
          </p>
        </div>
      </div>
    </div>
  );
}
