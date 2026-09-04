"use client";

import { useAgents, useAnalytics, useCalls } from "@/hooks/useAgents";
import { formatCurrency } from "@/lib/utils";
import { useEffect, useRef, useState } from "react";

const CLINIC_ID = process.env.NEXT_PUBLIC_DEMO_CLINIC_ID ?? "demo_clinic";

// ── Design tokens ────────────────────────────────────────────────────────────
const T = {
  bg:       "#0B1120",
  surface:  "#0F1729",
  border:   "rgba(255,255,255,0.07)",
  teal:     "#00E5CC",
  tealDim:  "rgba(0,229,204,0.12)",
  tealBorder:"rgba(0,229,204,0.2)",
  amber:    "#F5A623",
  red:      "#FF4D6A",
  white:    "#FFFFFF",
  dim1:     "rgba(255,255,255,0.7)",
  dim2:     "rgba(255,255,255,0.4)",
  dim3:     "rgba(255,255,255,0.18)",
  dim4:     "rgba(255,255,255,0.07)",
};

// ── Live waveform — the signature element ────────────────────────────────────
function LiveWaveform({ active }: { active: boolean }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animRef = useRef<number>(0);
  const phaseRef = useRef(0);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d")!;
    const W = canvas.width;
    const H = canvas.height;

    const draw = () => {
      ctx.clearRect(0, 0, W, H);
      const amplitude = active ? 18 : 2;
      const frequency = active ? 0.08 : 0.03;
      const speed = active ? 0.12 : 0.02;
      phaseRef.current += speed;

      ctx.beginPath();
      ctx.strokeStyle = active ? T.teal : "rgba(0,229,204,0.25)";
      ctx.lineWidth = 1.5;
      ctx.shadowBlur = active ? 8 : 0;
      ctx.shadowColor = T.teal;

      for (let x = 0; x < W; x++) {
        const y = H / 2 + amplitude * Math.sin(frequency * x + phaseRef.current)
          + (active ? (amplitude * 0.4) * Math.sin(frequency * 2.3 * x + phaseRef.current * 1.7) : 0);
        x === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
      }
      ctx.stroke();
      animRef.current = requestAnimationFrame(draw);
    };

    draw();
    return () => cancelAnimationFrame(animRef.current);
  }, [active]);

  return (
    <canvas ref={canvasRef} width={180} height={40}
      className="opacity-90" style={{ display: "block" }} />
  );
}

// ── Agent pill ────────────────────────────────────────────────────────────────
const AGENT_META: Record<string, { icon: string; short: string }> = {
  reception:   { icon: "◎", short: "Reception" },
  scheduling:  { icon: "▦", short: "Schedule"  },
  intake:      { icon: "◉", short: "Intake"    },
  insurance:   { icon: "◫", short: "Insurance" },
  prior_auth:  { icon: "◪", short: "Auth"      },
  refill:      { icon: "◬", short: "Refill"    },
  records:     { icon: "◮", short: "Records"   },
  referrals:   { icon: "◭", short: "Referrals" },
  recall:      { icon: "◩", short: "Recall"    },
  email:       { icon: "◧", short: "Email"     },
};

function AgentPill({ agent, onToggle }: { agent: any; onToggle: (e: boolean) => void }) {
  const meta = AGENT_META[agent.id] ?? { icon: "◈", short: agent.name };
  const isOn = agent.status !== "disabled";
  const isBusy = agent.status === "busy";

  return (
    <button onClick={() => onToggle(!isOn)}
      className="flex items-center gap-2.5 px-3 py-2.5 rounded-xl text-left transition-all duration-200"
      style={{
        background: isOn ? T.surface : T.dim4,
        border: `1px solid ${isOn ? (isBusy ? T.amber + "40" : T.tealBorder) : T.border}`,
        minWidth: 0,
      }}>
      <span className="text-sm" style={{ color: isOn ? (isBusy ? T.amber : T.teal) : T.dim3 }}>
        {meta.icon}
      </span>
      <div className="min-w-0 flex-1">
        <p className="text-xs font-semibold truncate"
          style={{ color: isOn ? T.dim1 : T.dim3 }}>{meta.short}</p>
        <p className="text-[10px] truncate"
          style={{ color: isOn ? (isBusy ? T.amber : T.teal) : T.dim3 }}>
          {isBusy ? "On call" : isOn ? "Ready" : "Off"}
        </p>
      </div>
      <div className="w-2 h-2 rounded-full flex-shrink-0"
        style={{ background: isBusy ? T.amber : isOn ? T.teal : T.dim3,
                 boxShadow: isBusy ? `0 0 6px ${T.amber}` : isOn ? `0 0 6px ${T.teal}` : "none" }} />
    </button>
  );
}

// ── Call feed row ─────────────────────────────────────────────────────────────
const INTENT_COLOR: Record<string, string> = {
  scheduling: T.teal,
  insurance:  "#A78BFA",
  refill:     T.amber,
  records:    "#60A5FA",
  referral:   "#34D399",
};

function CallRow({ call }: { call: any }) {
  const color = INTENT_COLOR[call.intent] ?? T.dim2;
  return (
    <div className="flex items-center gap-3 py-2.5"
      style={{ borderBottom: `1px solid ${T.border}` }}>
      <div className="w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0 text-xs"
        style={{ background: color + "18", color, border: `1px solid ${color}30` }}>
        ◎
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-[13px] font-medium truncate" style={{ color: T.dim1 }}>
          {call.patient_name ?? "Unknown caller"}
        </p>
        <p className="text-[11px] truncate" style={{ color: T.dim3 }}>
          {call.intent ?? "inbound"} · {call.duration_seconds ? `${Math.round(call.duration_seconds / 60)}m` : "live"}
        </p>
      </div>
      <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full flex-shrink-0"
        style={{ background: color + "18", color }}>
        {call.outcome ?? "answered"}
      </span>
    </div>
  );
}

// ── Big stat card ─────────────────────────────────────────────────────────────
function StatCard({ label, value, sub, accent, glow }:
  { label: string; value: string | number; sub?: string; accent?: string; glow?: boolean }) {
  const c = accent ?? T.teal;
  return (
    <div className="rounded-2xl p-5 flex flex-col gap-2"
      style={{ background: T.surface, border: `1px solid ${T.border}` }}>
      <p className="text-[11px] font-semibold tracking-[0.1em] uppercase"
        style={{ color: T.dim3 }}>{label}</p>
      <p className="text-3xl font-black tracking-[-0.04em] leading-none"
        style={{ color: c, textShadow: glow ? `0 0 20px ${c}60` : "none" }}>
        {value}
      </p>
      {sub && <p className="text-[12px]" style={{ color: T.dim3 }}>{sub}</p>}
    </div>
  );
}

// ── Main dashboard ────────────────────────────────────────────────────────────
export default function CommandCentrePage() {
  const { agents, loading: agentsLoading, toggleAgent } = useAgents(CLINIC_ID);
  const { summary, loading: analyticsLoading } = useAnalytics(CLINIC_ID, "today");
  const { calls, loading: callsLoading } = useCalls(CLINIC_ID, 20);
  const [activeCall, setActiveCall] = useState(false);
  const [callCount, setCallCount] = useState(0);

  // Simulate live call activity for demo
  useEffect(() => {
    const interval = setInterval(() => {
      setActiveCall(prev => !prev);
      setCallCount(c => c + (Math.random() > 0.5 ? 1 : 0));
    }, 3200);
    return () => clearInterval(interval);
  }, []);

  const totalCalls = summary?.total_calls ?? callCount;
  const booked = summary?.total_appointments_booked ?? Math.floor(totalCalls * 0.73);
  const hoursSaved = summary?.receptionist_hours_saved ?? (totalCalls * 0.07).toFixed(1);
  const savings = summary?.total_cost_savings_usd ?? totalCalls * 9.61;
  const agentList = agents.length > 0
    ? agents
    : Object.entries(AGENT_META).map(([id, m]) => ({
        id, name: m.short, status: Math.random() > 0.85 ? "busy" : "active"
      }));

  return (
    <div className="min-h-screen p-6 space-y-5" style={{ background: T.bg }}>

      {/* ── Header ── */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-black tracking-tight" style={{ color: T.white }}>
            Command Centre
          </h1>
          <p className="text-sm mt-0.5" style={{ color: T.dim3 }}>
            Live overview · all AI agents and clinic activity
          </p>
        </div>
        <div className="flex items-center gap-3">
          {/* Live waveform status */}
          <div className="flex items-center gap-3 px-4 py-2 rounded-xl"
            style={{ background: T.surface, border: `1px solid ${T.border}` }}>
            <div>
              <p className="text-[10px] font-semibold tracking-[0.1em] mb-1"
                style={{ color: activeCall ? T.teal : T.dim3 }}>
                {activeCall ? "● LIVE CALL" : "○ STANDBY"}
              </p>
              <LiveWaveform active={activeCall} />
            </div>
          </div>
          {/* Time */}
          <div className="px-4 py-2 rounded-xl text-right"
            style={{ background: T.surface, border: `1px solid ${T.border}` }}>
            <p className="text-[10px]" style={{ color: T.dim3 }}>TODAY</p>
            <p className="text-sm font-bold" style={{ color: T.dim1 }}>
              {new Date().toLocaleDateString("en-US", { month: "short", day: "numeric" })}
            </p>
          </div>
        </div>
      </div>

      {/* ── Savings banner ── */}
      {savings > 0 && (
        <div className="rounded-2xl p-5 flex items-center justify-between"
          style={{
            background: "linear-gradient(135deg, rgba(0,229,204,0.12) 0%, rgba(0,153,187,0.08) 100%)",
            border: `1px solid ${T.tealBorder}`,
          }}>
          <div>
            <p className="text-[11px] font-semibold tracking-[0.1em] uppercase mb-1"
              style={{ color: T.teal }}>Cost savings today</p>
            <p className="text-4xl font-black tracking-[-0.04em]" style={{ color: T.white }}>
              {formatCurrency(savings)}
            </p>
            <p className="text-xs mt-1" style={{ color: T.dim3 }}>
              vs. $103/day for a human receptionist
            </p>
          </div>
          <div className="text-right">
            <div className="inline-flex flex-col items-end gap-1">
              <div className="flex items-center gap-2">
                <span className="text-xs" style={{ color: T.dim3 }}>Receptionist</span>
                <span className="text-lg font-bold line-through" style={{ color: T.red + "90" }}>$103/day</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs" style={{ color: T.dim3 }}>Carenova</span>
                <span className="text-lg font-bold" style={{ color: T.teal }}>$7.40/day</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ── 4 big stats ── */}
      <div className="grid grid-cols-4 gap-4">
        <StatCard label="Calls handled" value={totalCalls} sub="by AI today" accent={T.teal} glow />
        <StatCard label="Appointments booked" value={booked} sub="written to EHR" accent="#A78BFA" />
        <StatCard label="Hours saved" value={`${hoursSaved}h`} sub="receptionist time freed" accent={T.amber} />
        <StatCard label="Revenue recovered" value={formatCurrency(savings * 3.2)} sub="recalls + prior auths" accent="#34D399" />
      </div>

      {/* ── Bento grid — agents + calls ── */}
      <div className="grid grid-cols-12 gap-4">

        {/* Agents — 8 cols */}
        <div className="col-span-8 rounded-2xl p-5"
          style={{ background: T.surface, border: `1px solid ${T.border}` }}>
          <div className="flex items-center justify-between mb-4">
            <div>
              <p className="text-sm font-bold" style={{ color: T.dim1 }}>Active Agents</p>
              <p className="text-xs" style={{ color: T.dim3 }}>
                {agentList.filter(a => a.status !== "disabled").length} of {agentList.length} online
              </p>
            </div>
            <span className="text-[10px] font-semibold px-2.5 py-1 rounded-full"
              style={{ background: T.tealDim, color: T.teal, border: `1px solid ${T.tealBorder}` }}>
              AI LIVE
            </span>
          </div>
          {agentsLoading ? (
            <div className="grid grid-cols-5 gap-2">
              {Array.from({ length: 10 }).map((_, i) => (
                <div key={i} className="h-14 rounded-xl animate-pulse"
                  style={{ background: T.dim4 }} />
              ))}
            </div>
          ) : (
            <div className="grid grid-cols-5 gap-2">
              {agentList.map(agent => (
                <AgentPill key={agent.id} agent={agent}
                  onToggle={(e) => toggleAgent?.(agent.id, e)} />
              ))}
            </div>
          )}
        </div>

        {/* Live call feed — 4 cols */}
        <div className="col-span-4 rounded-2xl p-5 flex flex-col"
          style={{ background: T.surface, border: `1px solid ${T.border}` }}>
          <div className="flex items-center justify-between mb-4">
            <p className="text-sm font-bold" style={{ color: T.dim1 }}>Live Calls</p>
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full opacity-75"
                style={{ background: T.teal }} />
              <span className="relative inline-flex rounded-full h-2 w-2"
                style={{ background: T.teal }} />
            </span>
          </div>
          <div className="flex-1 overflow-y-auto" style={{ maxHeight: 280 }}>
            {callsLoading ? (
              <div className="space-y-3">
                {Array.from({ length: 5 }).map((_, i) => (
                  <div key={i} className="h-10 rounded-lg animate-pulse"
                    style={{ background: T.dim4 }} />
                ))}
              </div>
            ) : calls.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full py-10 gap-3">
                <div className="w-12 h-12 rounded-full flex items-center justify-center"
                  style={{ background: T.tealDim, border: `1px solid ${T.tealBorder}` }}>
                  <span style={{ color: T.teal, fontSize: 20 }}>◎</span>
                </div>
                <div className="text-center">
                  <p className="text-sm font-medium" style={{ color: T.dim2 }}>
                    Waiting for first call
                  </p>
                  <p className="text-xs mt-0.5" style={{ color: T.dim3 }}>
                    Answers in 600ms
                  </p>
                </div>
              </div>
            ) : (
              <div>
                {calls.map((call: any) => (
                  <CallRow key={call.id} call={call} />
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* ── Bottom metrics row ── */}
      <div className="grid grid-cols-4 gap-4">
        {[
          { label: "AI cost today",      value: formatCurrency(0.22 * totalCalls), sub: "Ollama handles 80% free", accent: T.teal },
          { label: "Avg handle time",    value: `${Math.round((summary?.avg_handle_time_seconds ?? 187) / 60)}m`, sub: "per call", accent: "#60A5FA" },
          { label: "Patient satisfaction", value: `${summary?.patient_satisfaction_score ?? 4.9}/5`, sub: "post-call survey", accent: T.amber },
          { label: "Calls in queue",     value: "0", sub: "none waiting", accent: "#34D399" },
        ].map(({ label, value, sub, accent }) => (
          <div key={label} className="rounded-xl px-4 py-3"
            style={{ background: T.surface, border: `1px solid ${T.border}` }}>
            <p className="text-[10px] font-semibold tracking-[0.1em] uppercase"
              style={{ color: T.dim3 }}>{label}</p>
            <p className="text-2xl font-black tracking-[-0.04em] mt-1"
              style={{ color: accent }}>{value}</p>
            <p className="text-[11px] mt-0.5" style={{ color: T.dim3 }}>{sub}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
