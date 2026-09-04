"use client";
import { useState, useEffect } from "react";
import api from "@/lib/api";
import type { Appointment } from "@/types/patient";
import { formatDateTime } from "@/lib/utils";

const CLINIC_ID = process.env.NEXT_PUBLIC_DEMO_CLINIC_ID ?? "demo_clinic";
const T = {
  bg:"#0B1120",surface:"#0F1729",border:"rgba(255,255,255,0.07)",
  teal:"#00E5CC",tealDim:"rgba(0,229,204,0.12)",tealBorder:"rgba(0,229,204,0.2)",
  amber:"#F5A623",green:"#34D399",purple:"#A78BFA",red:"#FF4D6A",
  white:"#FFFFFF",dim1:"rgba(255,255,255,0.75)",dim2:"rgba(255,255,255,0.45)",
  dim3:"rgba(255,255,255,0.2)",dim4:"rgba(255,255,255,0.06)",
};

const STATUS_COLORS: Record<string,{color:string;bg:string}> = {
  scheduled:  { color:T.teal,   bg:T.tealDim },
  confirmed:  { color:T.green,  bg:"rgba(52,211,153,0.12)" },
  completed:  { color:"rgba(255,255,255,0.3)", bg:"rgba(255,255,255,0.06)" },
  cancelled:  { color:T.red,    bg:"rgba(255,77,106,0.12)" },
  no_show:    { color:T.amber,  bg:"rgba(245,166,35,0.12)" },
};

const DEMO_APPTS = [
  { id:"A1", patient_name:"Maria Santos",   provider_name:"Dr. Chen",    appointment_datetime:"2026-07-01T09:00:00", reason:"Annual physical",    status:"confirmed",  duration_minutes:45 },
  { id:"A2", patient_name:"James Mitchell", provider_name:"Dr. Kim",     appointment_datetime:"2026-07-01T10:30:00", reason:"Follow-up HTN",      status:"scheduled",  duration_minutes:20 },
  { id:"A3", patient_name:"Priya Sharma",   provider_name:"Dr. Chen",    appointment_datetime:"2026-07-01T11:00:00", reason:"New patient",        status:"confirmed",  duration_minutes:60 },
  { id:"A4", patient_name:"Amaka Obi",      provider_name:"Dr. Adeyemi", appointment_datetime:"2026-07-01T14:00:00", reason:"Diabetes checkup",   status:"scheduled",  duration_minutes:30 },
  { id:"A5", patient_name:"Robert Chen",    provider_name:"Dr. Kim",     appointment_datetime:"2026-07-01T15:30:00", reason:"Medication review",  status:"scheduled",  duration_minutes:20 },
];

export default function AppointmentsPage() {
  const [appts, setAppts] = useState<Appointment[]>([]);
  const [loading, setLoading] = useState(true);
  const [view, setView] = useState<"list"|"day">("list");

  useEffect(() => {
    api.appointments.list(CLINIC_ID)
      .then(setAppts).catch(() => setAppts([])).finally(() => setLoading(false));
  }, []);

  const displayAppts = appts.length > 0 ? appts : DEMO_APPTS as any;

  return (
    <div style={{ minHeight:"100vh", padding:24, background:T.bg, display:"flex", flexDirection:"column", gap:18 }}>
      <div style={{ display:"flex", alignItems:"center", justifyContent:"space-between" }}>
        <div>
          <h1 style={{ fontSize:20, fontWeight:900, color:T.white }}>Schedule</h1>
          <p style={{ fontSize:13, color:T.dim3, marginTop:2 }}>
            {new Date().toLocaleDateString("en-US",{weekday:"long",month:"long",day:"numeric"})}
          </p>
        </div>
        <div style={{ display:"flex", gap:10, alignItems:"center" }}>
          <div style={{ display:"flex", gap:2, background:T.surface, border:`1px solid ${T.border}`, borderRadius:12, padding:4 }}>
            {(["list","day"] as const).map(v => (
              <button key={v} onClick={() => setView(v)}
                style={{ padding:"7px 16px", borderRadius:9, fontSize:12, fontWeight:600, cursor:"pointer", border:"none",
                         background:view===v ? T.tealDim : "transparent", color:view===v ? T.teal : T.dim3 }}>
                {v==="list" ? "List" : "Day view"}
              </button>
            ))}
          </div>
          <button style={{ background:T.tealDim, border:`1px solid ${T.tealBorder}`, borderRadius:12,
                           padding:"9px 18px", color:T.teal, fontSize:13, fontWeight:600, cursor:"pointer" }}>
            + Book Appointment
          </button>
        </div>
      </div>

      {/* Today stats */}
      <div style={{ display:"grid", gridTemplateColumns:"repeat(4,1fr)", gap:14 }}>
        {[
          { label:"Total today",    value:displayAppts.length,                                               color:T.teal   },
          { label:"Confirmed",      value:displayAppts.filter((a:any)=>a.status==="confirmed").length,       color:T.green  },
          { label:"Booked by AI",   value:displayAppts.length,                                               color:T.purple },
          { label:"No-shows",       value:displayAppts.filter((a:any)=>a.status==="no_show").length,         color:T.amber  },
        ].map(s => (
          <div key={s.label} style={{ background:T.surface, border:`1px solid ${T.border}`, borderRadius:14, padding:18 }}>
            <p style={{ fontSize:10, fontWeight:700, letterSpacing:"0.1em", textTransform:"uppercase", color:T.dim3 }}>{s.label}</p>
            <p style={{ fontSize:28, fontWeight:900, color:s.color, marginTop:6, letterSpacing:"-0.04em" }}>{s.value}</p>
          </div>
        ))}
      </div>

      {/* Appointment list */}
      <div style={{ background:T.surface, border:`1px solid ${T.border}`, borderRadius:18, overflow:"hidden" }}>
        <table style={{ width:"100%", borderCollapse:"collapse" }}>
          <thead>
            <tr style={{ borderBottom:`1px solid ${T.border}` }}>
              {["Patient","Provider","Time","Reason","Duration","Status"].map(h => (
                <th key={h} style={{ textAlign:"left", padding:"12px 20px", fontSize:10,
                                     fontWeight:700, letterSpacing:"0.1em", textTransform:"uppercase", color:T.dim3 }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {loading ? (
              Array.from({length:5}).map((_,i) => (
                <tr key={i} style={{ borderBottom:`1px solid ${T.border}` }}>
                  {Array.from({length:6}).map((_,j) => (
                    <td key={j} style={{ padding:"12px 20px" }}>
                      <div style={{ height:14, borderRadius:6, background:T.dim4, width:80 }} />
                    </td>
                  ))}
                </tr>
              ))
            ) : displayAppts.map((a:any, i:number) => {
              const sc = STATUS_COLORS[a.status] ?? STATUS_COLORS.scheduled;
              return (
                <tr key={a.id} style={{ borderBottom:i<displayAppts.length-1?`1px solid ${T.border}`:"none" }}>
                  <td style={{ padding:"12px 20px", fontSize:13, fontWeight:600, color:T.dim1 }}>{a.patient_name??"-"}</td>
                  <td style={{ padding:"12px 20px", fontSize:13, color:T.dim2 }}>{a.provider_name??"-"}</td>
                  <td style={{ padding:"12px 20px", fontSize:12, fontFamily:"monospace", color:T.dim2 }}>
                    {a.appointment_datetime ? new Date(a.appointment_datetime).toLocaleTimeString([],{hour:"2-digit",minute:"2-digit"}) : "-"}
                  </td>
                  <td style={{ padding:"12px 20px", fontSize:13, color:T.dim2 }}>{a.reason??"-"}</td>
                  <td style={{ padding:"12px 20px", fontSize:13, color:T.dim3 }}>{a.duration_minutes??20}min</td>
                  <td style={{ padding:"12px 20px" }}>
                    <span style={{ fontSize:11, fontWeight:600, padding:"3px 10px", borderRadius:100,
                                   background:sc.bg, color:sc.color, textTransform:"capitalize" }}>
                      {a.status??"-"}
                    </span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
