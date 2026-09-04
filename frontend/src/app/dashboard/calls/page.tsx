"use client";
import { useCalls } from "@/hooks/useAgents";

const T = {
  bg: "#0B1120", surface: "#0F1729", border: "rgba(255,255,255,0.07)",
  teal: "#00E5CC", tealDim: "rgba(0,229,204,0.12)", tealBorder: "rgba(0,229,204,0.2)",
  white: "#FFFFFF", dim1: "rgba(255,255,255,0.7)", dim2: "rgba(255,255,255,0.4)",
  dim3: "rgba(255,255,255,0.18)", dim4: "rgba(255,255,255,0.07)",
  amber: "#F5A623", green: "#34D399", purple: "#A78BFA",
};

const CLINIC_ID = process.env.NEXT_PUBLIC_DEMO_CLINIC_ID ?? "demo_clinic";

const INTENT_COLORS: Record<string, string> = {
  scheduling: T.teal,
  insurance: T.purple,
  refill: T.amber,
  records: "#60A5FA",
  referral: T.green,
};

const OUTCOME_CONFIG: Record<string, { color: string; label: string }> = {
  booked:    { color: T.teal,   label: "Booked" },
  resolved:  { color: T.green,  label: "Resolved" },
  transferred: { color: T.amber, label: "Transferred" },
  voicemail: { color: T.dim3,   label: "Voicemail" },
};

export default function CallsPage() {
  const { calls, loading } = useCalls(CLINIC_ID, 100);

  const stats = {
    total: calls.length,
    booked: calls.filter((c: any) => c.outcome === "booked").length,
    avgDuration: calls.length
      ? Math.round(calls.reduce((s: number, c: any) => s + (c.duration_seconds ?? 187), 0) / calls.length / 60)
      : 0,
  };

  return (
    <div className="min-h-screen p-6 space-y-5" style={{ background: T.bg }}>
      <div>
        <h1 className="text-xl font-black tracking-tight" style={{ color: T.white }}>Call Log</h1>
        <p className="text-sm mt-0.5" style={{ color: T.dim3 }}>All inbound and outbound calls</p>
      </div>

      {/* Quick stats */}
      <div className="grid grid-cols-3 gap-4">
        {[
          { label: "Total calls today", value: stats.total, color: T.teal },
          { label: "Appointments booked", value: stats.booked, color: T.green },
          { label: "Avg call duration", value: `${stats.avgDuration}m`, color: T.amber },
        ].map(s => (
          <div key={s.label} className="rounded-2xl p-5"
            style={{ background: T.surface, border: `1px solid ${T.border}` }}>
            <p className="text-[10px] font-semibold tracking-[0.1em] uppercase mb-1"
              style={{ color: T.dim3 }}>{s.label}</p>
            <p className="text-3xl font-black tracking-[-0.04em]" style={{ color: s.color }}>
              {s.value}
            </p>
          </div>
        ))}
      </div>

      {/* Call table */}
      <div className="rounded-2xl overflow-hidden"
        style={{ background: T.surface, border: `1px solid ${T.border}` }}>
        <table className="w-full">
          <thead>
            <tr style={{ borderBottom: `1px solid ${T.border}` }}>
              {["Patient", "Intent", "Duration", "Outcome", "Agent", "Time"].map(h => (
                <th key={h} className="text-left px-5 py-3.5 text-[10px] font-semibold tracking-[0.1em] uppercase"
                  style={{ color: T.dim3 }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {loading ? (
              Array.from({ length: 8 }).map((_, i) => (
                <tr key={i} style={{ borderBottom: `1px solid ${T.border}` }}>
                  {Array.from({ length: 6 }).map((_, j) => (
                    <td key={j} className="px-5 py-3.5">
                      <div className="h-4 rounded-lg animate-pulse w-20"
                        style={{ background: T.dim4 }} />
                    </td>
                  ))}
                </tr>
              ))
            ) : calls.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-5 py-16 text-center">
                  <div className="flex flex-col items-center gap-3">
                    <div className="w-12 h-12 rounded-full flex items-center justify-center text-xl"
                      style={{ background: T.tealDim, border: `1px solid ${T.tealBorder}`, color: T.teal }}>
                      ◎
                    </div>
                    <p className="text-sm font-medium" style={{ color: T.dim2 }}>No calls yet</p>
                    <p className="text-xs" style={{ color: T.dim3 }}>
                      Carenova will answer every call in 600ms
                    </p>
                  </div>
                </td>
              </tr>
            ) : (
              calls.map((call: any) => {
                const intentColor = INTENT_COLORS[call.intent] ?? T.dim3;
                const outcome = OUTCOME_CONFIG[call.outcome] ?? { color: T.dim3, label: call.outcome ?? "—" };
                return (
                  <tr key={call.id} className="transition-colors"
                    style={{ borderBottom: `1px solid ${T.border}` }}>
                    <td className="px-5 py-3.5 text-sm font-semibold" style={{ color: T.dim1 }}>
                      {call.patient_name ?? "Unknown"}
                    </td>
                    <td className="px-5 py-3.5">
                      <span className="text-[11px] font-semibold px-2 py-0.5 rounded-full"
                        style={{ background: intentColor + "18", color: intentColor, border: `1px solid ${intentColor}30` }}>
                        {call.intent ?? "inbound"}
                      </span>
                    </td>
                    <td className="px-5 py-3.5 text-sm font-mono" style={{ color: T.dim2 }}>
                      {call.duration_seconds ? `${Math.round(call.duration_seconds / 60)}m ${call.duration_seconds % 60}s` : "—"}
                    </td>
                    <td className="px-5 py-3.5">
                      <span className="text-[11px] font-semibold px-2 py-0.5 rounded-full"
                        style={{ background: outcome.color + "18", color: outcome.color, border: `1px solid ${outcome.color}30` }}>
                        {outcome.label}
                      </span>
                    </td>
                    <td className="px-5 py-3.5 text-sm capitalize" style={{ color: T.dim2 }}>
                      {call.agent_type ?? "reception"}
                    </td>
                    <td className="px-5 py-3.5 text-sm font-mono" style={{ color: T.dim3 }}>
                      {call.created_at ? new Date(call.created_at).toLocaleTimeString() : "—"}
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
