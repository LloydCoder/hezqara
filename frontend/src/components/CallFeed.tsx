"use client";

import { formatDateTime, formatDuration, intentLabel } from "@/lib/utils";
import type { Call } from "@/types/patient";

interface CallFeedProps {
  calls: Call[];
  loading?: boolean;
}

export function CallFeed({ calls, loading }: CallFeedProps) {
  if (loading) {
    return (
      <div className="space-y-3">
        {[...Array(5)].map((_, i) => (
          <div key={i} className="h-14 bg-slate-100 rounded-lg animate-pulse" />
        ))}
      </div>
    );
  }

  if (calls.length === 0) {
    return (
      <div className="text-center py-10 text-slate-400 text-sm">
        No calls yet today
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {calls.map((call) => (
        <div
          key={call.id}
          className="flex items-center justify-between px-4 py-3 bg-white rounded-lg border border-slate-200 hover:border-slate-300 transition-colors"
        >
          <div className="flex items-center gap-3">
            {/* Direction indicator */}
            <div className="w-7 h-7 rounded-full bg-slate-100 flex items-center justify-center text-xs">
              {call.call_type === "inbound" ? "↙" : "↗"}
            </div>
            <div>
              <p className="text-sm font-medium text-slate-800">
                {call.patient_name ?? "Unknown Caller"}
              </p>
              <p className="text-xs text-slate-500">
                {call.started_at ? formatDateTime(call.started_at) : "—"}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-4 text-right">
            <div>
              <p className="text-xs text-slate-500">Intent</p>
              <p className="text-xs font-medium text-slate-700">
                {intentLabel(call.intent)}
              </p>
            </div>
            <div>
              <p className="text-xs text-slate-500">Duration</p>
              <p className="text-xs font-medium text-slate-700">
                {call.duration_ms ? formatDuration(call.duration_ms) : "—"}
              </p>
            </div>
            <div>
              <p className="text-xs text-slate-500">Agent</p>
              <p className="text-xs font-medium text-slate-700 capitalize">
                {call.agent_type}
              </p>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
