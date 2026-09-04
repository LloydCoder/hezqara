"use client";
import { useState, useEffect, useCallback } from "react";

const T = {
  bg: "#0B1120", surface: "#0F1729", surfaceHi: "#141E35",
  border: "rgba(255,255,255,0.07)", borderHi: "rgba(255,255,255,0.14)",
  teal: "#00E5CC", tealDim: "rgba(0,229,204,0.12)", tealBorder: "rgba(0,229,204,0.2)",
  amber: "#F5A623", amberDim: "rgba(245,166,35,0.12)",
  red: "#FF4D6A", redDim: "rgba(255,77,106,0.12)",
  green: "#34D399", greenDim: "rgba(52,211,153,0.12)",
  purple: "#A78BFA", white: "#FFFFFF",
  dim1: "rgba(255,255,255,0.78)", dim2: "rgba(255,255,255,0.48)",
  dim3: "rgba(255,255,255,0.22)", dim4: "rgba(255,255,255,0.07)",
};

const CLINIC_ID = process.env.NEXT_PUBLIC_DEMO_CLINIC_ID ?? "demo_clinic_ng";
const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "/api";

const LANG_FLAGS: Record<string, string> = {
  en: "🇬🇧", ig: "🟢", yo: "🟡", ha: "🔵", fr: "🇫🇷",
  sw: "🇰🇪", hi: "🇮🇳", fil: "🇵🇭", ar: "🇦🇪",
};

function PingDot({ color = T.teal, size = 8 }: { color?: string; size?: number }) {
  return (
    <span style={{ position: "relative", display: "inline-flex", width: size, height: size }}>
      <span style={{
        position: "absolute", inset: 0, borderRadius: "50%", background: color,
        opacity: 0.7, animation: "ping 1.4s cubic-bezier(0,0,0.2,1) infinite",
      }} />
      <span style={{ position: "relative", width: size, height: size, borderRadius: "50%", background: color }} />
    </span>
  );
}

function StatBox({ label, value, sub, color }: { label: string; value: string | number; sub?: string; color: string }) {
  return (
    <div style={{ background: T.surface, border: `1px solid ${T.border}`, borderRadius: 14, padding: "16px 18px" }}>
      <p style={{ fontSize: 10, fontWeight: 700, letterSpacing: "0.1em", textTransform: "uppercase", color: T.dim3, marginBottom: 6 }}>{label}</p>
      <p style={{ fontSize: 28, fontWeight: 900, letterSpacing: "-0.04em", color, lineHeight: 1 }}>{value}</p>
      {sub && <p style={{ fontSize: 11, color: T.dim3, marginTop: 4 }}>{sub}</p>}
    </div>
  );
}

interface QueueEntry {
  visit_id: string;
  queue_number: number;
  patient_name: string;
  patient_phone?: string;
  chief_complaint: string;
  priority: string;
  status: string;
  wait_minutes: number;
  language: string;
}

interface CalledEntry {
  visit_id: string;
  queue_number: number;
  patient_name: string;
  room?: string;
  provider_id?: string;
}

export default function WalkInQueuePage() {
  const [waiting, setWaiting] = useState<QueueEntry[]>([]);
  const [called, setCalled] = useState<CalledEntry[]>([]);
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [qrLanguage, setQrLanguage] = useState("en");

  const fetchQueue = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/walkin/queue/${CLINIC_ID}`);
      const data = await res.json();
      setWaiting(data.waiting ?? []);
      setCalled(data.called ?? []);
    } catch (e) {
      console.error("Failed to fetch queue", e);
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchStats = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/walkin/queue/${CLINIC_ID}/stats`);
      const data = await res.json();
      setStats(data);
    } catch (e) {
      console.error("Failed to fetch stats", e);
    }
  }, []);

  useEffect(() => {
    fetchQueue();
    fetchStats();
    const interval = setInterval(() => { fetchQueue(); fetchStats(); }, 5000);
    return () => clearInterval(interval);
  }, [fetchQueue, fetchStats]);

  const callNext = async () => {
    try {
      await fetch(`${API_BASE}/walkin/queue/${CLINIC_ID}/next`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ provider_id: "PROV-001", room: "Room 1" }),
      });
      fetchQueue();
      fetchStats();
    } catch (e) {
      console.error("Failed to call next patient", e);
    }
  };

  const completeVisit = async (visitId: string, followUpDays: number | null) => {
    try {
      await fetch(`${API_BASE}/walkin/queue/visit/${visitId}/complete`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ notes: "", follow_up_days: followUpDays }),
      });
      fetchQueue();
      fetchStats();
    } catch (e) {
      console.error("Failed to complete visit", e);
    }
  };

  const sortedWaiting = [...waiting].sort((a, b) => {
    if (a.priority === "emergency" && b.priority !== "emergency") return -1;
    if (b.priority === "emergency" && a.priority !== "emergency") return 1;
    return a.queue_number - b.queue_number;
  });

  const qrCodeUrl = `${API_BASE}/walkin/qr/${CLINIC_ID}?language=${qrLanguage}`;

  return (
    <div className="min-h-screen p-6 space-y-5" style={{ background: T.bg }}>
      <style>{`@keyframes ping { 75%, 100% { transform: scale(2); opacity: 0; } }`}</style>

      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-black tracking-tight" style={{ color: T.white }}>Walk-In Queue</h1>
          <p className="text-sm mt-0.5" style={{ color: T.dim3 }}>Live queue — patients check in via WhatsApp</p>
        </div>
        <div className="flex items-center gap-2">
          <PingDot />
          <span className="text-xs font-semibold" style={{ color: T.teal }}>Live</span>
        </div>
      </div>

      <div className="grid grid-cols-4 gap-3">
        <StatBox label="Waiting now" value={sortedWaiting.length} sub="in queue" color={T.teal} />
        <StatBox label="With doctor" value={called.length} sub="being seen" color={T.amber} />
        <StatBox label="Completed today" value={stats?.completed_today ?? 0} sub="discharged" color={T.green} />
        <StatBox label="Avg wait" value={`${stats?.avg_wait_minutes ?? 0}m`} sub="estimated" color={T.purple} />
      </div>

      <div className="grid gap-4" style={{ gridTemplateColumns: "1fr 320px" }}>

        <div className="flex flex-col gap-3">
          {called.length > 0 && (
            <div>
              <p className="text-[11px] font-bold tracking-wider uppercase mb-2" style={{ color: T.amber }}>With Doctor</p>
              <div className="flex flex-col gap-2">
                {called.map((e) => (
                  <div key={e.visit_id} className="flex items-center gap-3 rounded-xl px-4 py-3"
                    style={{ background: T.amberDim, border: `1px solid ${T.amber}40` }}>
                    <div className="w-9 h-9 rounded-lg flex items-center justify-center text-lg flex-shrink-0"
                      style={{ background: T.amber, color: "#070C17" }}>⚕</div>
                    <div className="flex-1">
                      <p className="text-sm font-bold" style={{ color: T.dim1 }}>{e.patient_name}</p>
                      <p className="text-xs" style={{ color: T.amber }}>With doctor · {e.room ?? "Room 1"}</p>
                    </div>
                    <button onClick={() => completeVisit(e.visit_id, 7)}
                      className="text-xs font-semibold px-3 py-1.5 rounded-lg"
                      style={{ background: T.greenDim, border: `1px solid ${T.green}30`, color: T.green }}>
                      ✓ Done
                    </button>
                    <button onClick={() => completeVisit(e.visit_id, null)}
                      className="text-xs px-3 py-1.5 rounded-lg"
                      style={{ background: T.dim4, border: `1px solid ${T.border}`, color: T.dim3 }}>
                      No-show
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div>
            <div className="flex items-center justify-between mb-2">
              <p className="text-[11px] font-bold tracking-wider uppercase" style={{ color: T.dim3 }}>
                Waiting ({sortedWaiting.length})
              </p>
              {sortedWaiting.length > 0 && called.length === 0 && (
                <button onClick={callNext}
                  className="text-xs font-bold px-4 py-1.5 rounded-lg"
                  style={{ background: "linear-gradient(135deg,#00E5CC,#0099BB)", color: "#070C17" }}>
                  Call Next →
                </button>
              )}
            </div>

            {loading ? (
              <div className="space-y-2">
                {Array.from({ length: 4 }).map((_, i) => (
                  <div key={i} className="h-16 rounded-xl animate-pulse" style={{ background: T.dim4 }} />
                ))}
              </div>
            ) : sortedWaiting.length === 0 ? (
              <div className="rounded-xl p-8 text-center" style={{ background: T.surface, border: `1px solid ${T.border}` }}>
                <p className="text-3xl mb-2">✅</p>
                <p className="text-sm font-bold" style={{ color: T.dim2 }}>Queue is empty</p>
                <p className="text-xs mt-1" style={{ color: T.dim3 }}>All patients have been seen</p>
              </div>
            ) : (
              <div className="flex flex-col gap-2">
                {sortedWaiting.map((entry, i) => {
                  const isEmergency = entry.priority === "emergency";
                  const isNext = i === 0 && called.length === 0;
                  return (
                    <div key={entry.visit_id} className="flex items-center gap-3 rounded-xl px-4 py-3" style={{
                      background: isEmergency ? T.redDim : isNext ? T.tealDim : T.dim4,
                      border: `1px solid ${isEmergency ? T.red + "60" : isNext ? T.tealBorder : T.border}`,
                    }}>
                      <div className="w-10 h-10 rounded-lg flex items-center justify-center text-base font-black flex-shrink-0" style={{
                        background: isEmergency ? T.red : isNext ? T.teal : T.surface,
                        color: isEmergency || isNext ? "#070C17" : T.dim3,
                      }}>
                        {isEmergency ? "🚨" : entry.queue_number}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-1.5">
                          <p className="text-sm font-bold truncate" style={{ color: T.dim1 }}>{entry.patient_name}</p>
                          <span className="text-xs">{LANG_FLAGS[entry.language] ?? "🌍"}</span>
                        </div>
                        <p className="text-xs truncate" style={{ color: T.dim3 }}>{entry.chief_complaint}</p>
                      </div>
                      <p className="text-xs flex-shrink-0" style={{ color: isEmergency ? T.red : T.dim3 }}>
                        {isEmergency ? "Priority" : `${entry.wait_minutes}m wait`}
                      </p>
                      {isNext && (
                        <button onClick={callNext}
                          className="text-xs font-bold px-3 py-1.5 rounded-lg flex-shrink-0"
                          style={{ background: "linear-gradient(135deg,#00E5CC,#0099BB)", color: "#070C17" }}>
                          Call →
                        </button>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>

        <div className="flex flex-col gap-3">
          <div className="rounded-2xl p-6 text-center" style={{ background: T.surface, border: `1px solid ${T.border}` }}>
            <p className="text-sm font-bold mb-1" style={{ color: T.dim1 }}>Walk-In QR Code</p>
            <p className="text-xs mb-4" style={{ color: T.dim3 }}>Print and place at reception</p>

            <div className="mx-auto mb-3" style={{ width: 180, height: 180, background: "#fff", borderRadius: 12, padding: 8 }}>
              <img src={qrCodeUrl} alt="Walk-in check-in QR code" className="w-full h-full object-contain" />
            </div>

            <select value={qrLanguage} onChange={(e) => setQrLanguage(e.target.value)}
              className="w-full text-xs rounded-lg px-3 py-2 mb-3 outline-none"
              style={{ background: T.dim4, border: `1px solid ${T.border}`, color: T.dim1 }}>
              <option value="en">🇬🇧 English</option>
              <option value="ig">🟢 Igbo</option>
              <option value="yo">🟡 Yoruba</option>
              <option value="ha">🔵 Hausa</option>
              <option value="fr">🇫🇷 French</option>
              <option value="sw">🇰🇪 Swahili</option>
              <option value="hi">🇮🇳 Hindi</option>
              <option value="fil">🇵🇭 Filipino</option>
            </select>

            <a href={qrCodeUrl} download={`carenova-checkin-${CLINIC_ID}.png`}
              className="block text-xs font-semibold py-2 rounded-lg"
              style={{ background: T.tealDim, border: `1px solid ${T.tealBorder}`, color: T.teal }}>
              ⬇ Download PNG
            </a>
          </div>

          <div className="rounded-2xl p-5" style={{ background: T.surface, border: `1px solid ${T.border}` }}>
            <p className="text-xs font-bold mb-3" style={{ color: T.dim1 }}>How it works</p>
            {[
              "Patient scans QR code at reception",
              "WhatsApp opens with check-in message",
              "They send name + reason for visit",
              "Queue number assigned automatically",
            ].map((step, i) => (
              <div key={i} className="flex gap-2 mb-2 last:mb-0">
                <div className="w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold flex-shrink-0"
                  style={{ background: T.tealDim, border: `1px solid ${T.tealBorder}`, color: T.teal }}>
                  {i + 1}
                </div>
                <p className="text-xs" style={{ color: T.dim2 }}>{step}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
