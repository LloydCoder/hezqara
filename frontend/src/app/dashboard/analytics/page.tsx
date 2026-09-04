"use client";
import { useState, useEffect } from "react";
import { useAnalytics } from "@/hooks/useAgents";

const CLINIC_ID = process.env.NEXT_PUBLIC_DEMO_CLINIC_ID ?? "demo_clinic";
const T = {
  bg:"#0B1120",surface:"#0F1729",border:"rgba(255,255,255,0.07)",
  teal:"#00E5CC",tealDim:"rgba(0,229,204,0.12)",tealBorder:"rgba(0,229,204,0.2)",
  amber:"#F5A623",green:"#34D399",purple:"#A78BFA",red:"#FF4D6A",blue:"#60A5FA",
  white:"#FFFFFF",dim1:"rgba(255,255,255,0.75)",dim2:"rgba(255,255,255,0.45)",
  dim3:"rgba(255,255,255,0.2)",dim4:"rgba(255,255,255,0.06)",
};

type Period = "today"|"week"|"month";

// Simple sparkline bar chart
function SparkBars({ data, color }: { data: number[]; color: string }) {
  const max = Math.max(...data, 1);
  return (
    <div style={{ display:"flex", alignItems:"flex-end", gap:3, height:48 }}>
      {data.map((v,i) => (
        <div key={i} style={{
          flex:1, borderRadius:3,
          background: i === data.length-1 ? color : color+"50",
          height:`${Math.max((v/max)*100,4)}%`,
          transition:"height 0.3s ease",
        }} />
      ))}
    </div>
  );
}

// Donut chart (SVG)
function Donut({ segments, size=80 }: { segments:{value:number;color:string;label:string}[]; size?:number }) {
  const total = segments.reduce((s,x) => s+x.value, 0) || 1;
  const r = 28; const cx = size/2; const cy = size/2;
  const circumference = 2*Math.PI*r;
  let offset = 0;
  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
      {segments.map((seg,i) => {
        const dash = (seg.value/total)*circumference;
        const gap  = circumference - dash;
        const el = (
          <circle key={i} cx={cx} cy={cy} r={r}
            fill="none" stroke={seg.color} strokeWidth={10}
            strokeDasharray={`${dash} ${gap}`}
            strokeDashoffset={-offset}
            transform={`rotate(-90 ${cx} ${cy})`} />
        );
        offset += dash;
        return el;
      })}
      <circle cx={cx} cy={cy} r={22} fill={T.surface} />
    </svg>
  );
}

const DEMO_HOURLY = [4,7,12,19,28,23,31,26,18,14,9,6];
const DEMO_WEEKLY = [89,102,95,118,134,98,112];
const DEMO_MONTHLY = [312,389,445,502,478,534,611,589,623,701,688,742];

const INTENT_DATA = [
  { label:"Scheduling", value:42, color:T.teal   },
  { label:"Refill",     value:23, color:T.amber   },
  { label:"Insurance",  value:15, color:T.purple  },
  { label:"Records",    value:12, color:T.blue    },
  { label:"Referral",   value:8,  color:T.green   },
];

export default function AnalyticsPage() {
  const [period, setPeriod] = useState<Period>("today");
  const { summary, loading } = useAnalytics(CLINIC_ID, period);
  const calls    = summary?.total_calls ?? (period==="today"?147:period==="week"?738:2847);
  const booked   = summary?.total_appointments_booked ?? Math.floor(calls*0.73);
  const savings  = summary?.total_cost_savings_usd ?? calls*9.61;
  const chartData = period==="today" ? DEMO_HOURLY : period==="week" ? DEMO_WEEKLY : DEMO_MONTHLY;

  return (
    <div style={{ minHeight:"100vh", padding:24, background:T.bg, display:"flex", flexDirection:"column", gap:18 }}>
      <div style={{ display:"flex", alignItems:"center", justifyContent:"space-between" }}>
        <div>
          <h1 style={{ fontSize:20, fontWeight:900, color:T.white, letterSpacing:"-0.02em" }}>Analytics</h1>
          <p style={{ fontSize:13, color:T.dim3, marginTop:2 }}>Revenue, performance, and cost savings</p>
        </div>
        <div style={{ display:"flex", gap:2, background:T.surface, border:`1px solid ${T.border}`, borderRadius:12, padding:4 }}>
          {(["today","week","month"] as Period[]).map(p => (
            <button key={p} onClick={() => setPeriod(p)}
              style={{
                padding:"7px 16px", borderRadius:9, fontSize:12, fontWeight:600,
                cursor:"pointer", border:"none", textTransform:"capitalize",
                background: period===p ? T.tealDim : "transparent",
                color:      period===p ? T.teal    : T.dim3,
                transition:"all 0.15s",
              }}>{p}</button>
          ))}
        </div>
      </div>

      {/* Top KPIs */}
      <div style={{ display:"grid", gridTemplateColumns:"repeat(4,1fr)", gap:14 }}>
        {[
          { label:"Total calls",       value:calls,              color:T.teal,   sub:"by AI" },
          { label:"Appointments made", value:booked,             color:T.purple, sub:"written to EHR" },
          { label:"Cost saved",        value:`$${savings.toFixed(0)}`, color:T.green, sub:"vs receptionist" },
          { label:"Conversion rate",   value:`${Math.round(booked/calls*100)}%`, color:T.amber, sub:"call → booked" },
        ].map(k => (
          <div key={k.label} style={{ background:T.surface, border:`1px solid ${T.border}`, borderRadius:16, padding:20 }}>
            <p style={{ fontSize:10, fontWeight:700, letterSpacing:"0.1em", textTransform:"uppercase", color:T.dim3 }}>{k.label}</p>
            <p style={{ fontSize:34, fontWeight:900, letterSpacing:"-0.04em", color:k.color, marginTop:6, lineHeight:1 }}>{k.value}</p>
            <p style={{ fontSize:11, color:T.dim3, marginTop:6 }}>{k.sub}</p>
          </div>
        ))}
      </div>

      {/* Call volume chart + intent breakdown */}
      <div style={{ display:"grid", gridTemplateColumns:"2fr 1fr", gap:14 }}>
        <div style={{ background:T.surface, border:`1px solid ${T.border}`, borderRadius:18, padding:24 }}>
          <div style={{ display:"flex", alignItems:"center", justifyContent:"space-between", marginBottom:20 }}>
            <div>
              <p style={{ fontSize:13, fontWeight:700, color:T.dim1 }}>Call Volume</p>
              <p style={{ fontSize:11, color:T.dim3 }}>
                {period==="today"?"Hourly":period==="week"?"Daily":"Monthly"} breakdown
              </p>
            </div>
            <span style={{ fontSize:22, fontWeight:900, letterSpacing:"-0.04em", color:T.teal }}>{calls}</span>
          </div>
          <SparkBars data={chartData} color={T.teal} />
          <div style={{ display:"flex", justifyContent:"space-between", marginTop:8 }}>
            {period==="today"
              ? ["9am","10am","11am","12pm","1pm","2pm","3pm","4pm","5pm","6pm","7pm","8pm"]
                  .filter((_,i) => i%2===0)
                  .map(l => <span key={l} style={{ fontSize:9, color:T.dim3 }}>{l}</span>)
              : period==="week"
              ? ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"].map(l => <span key={l} style={{ fontSize:9, color:T.dim3 }}>{l}</span>)
              : ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"].map(l => <span key={l} style={{ fontSize:9, color:T.dim3 }}>{l}</span>)
            }
          </div>
        </div>

        <div style={{ background:T.surface, border:`1px solid ${T.border}`, borderRadius:18, padding:24 }}>
          <p style={{ fontSize:13, fontWeight:700, color:T.dim1, marginBottom:16 }}>Call Intent</p>
          <div style={{ display:"flex", alignItems:"center", gap:16, marginBottom:20 }}>
            <Donut segments={INTENT_DATA} size={80} />
            <div style={{ flex:1 }}>
              {INTENT_DATA.map(d => (
                <div key={d.label} style={{ display:"flex", alignItems:"center", justifyContent:"space-between", marginBottom:6 }}>
                  <div style={{ display:"flex", alignItems:"center", gap:6 }}>
                    <div style={{ width:6, height:6, borderRadius:"50%", background:d.color }} />
                    <span style={{ fontSize:11, color:T.dim2 }}>{d.label}</span>
                  </div>
                  <span style={{ fontSize:11, fontWeight:700, color:d.color }}>{d.value}%</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* ROI + performance row */}
      <div style={{ display:"grid", gridTemplateColumns:"repeat(3,1fr)", gap:14 }}>
        {[
          { label:"Avg call duration",    value:"3m 07s", sub:"target < 5min",       color:T.blue,   progress:62 },
          { label:"AI confidence score",  value:"0.91",   sub:"autonomous threshold 0.85", color:T.green, progress:91 },
          { label:"Patient satisfaction", value:"4.9 / 5", sub:"post-call NPS",      color:T.amber,  progress:98 },
        ].map(m => (
          <div key={m.label} style={{ background:T.surface, border:`1px solid ${T.border}`, borderRadius:16, padding:20 }}>
            <p style={{ fontSize:10, fontWeight:700, letterSpacing:"0.1em", textTransform:"uppercase", color:T.dim3 }}>{m.label}</p>
            <p style={{ fontSize:28, fontWeight:900, letterSpacing:"-0.04em", color:m.color, margin:"8px 0 4px" }}>{m.value}</p>
            <p style={{ fontSize:11, color:T.dim3, marginBottom:12 }}>{m.sub}</p>
            <div style={{ height:4, borderRadius:4, background:T.dim4, overflow:"hidden" }}>
              <div style={{ height:"100%", width:`${m.progress}%`, background:m.color, borderRadius:4 }} />
            </div>
          </div>
        ))}
      </div>

      {/* Cost breakdown */}
      <div style={{ background:T.surface, border:`1px solid ${T.border}`, borderRadius:18, padding:24 }}>
        <p style={{ fontSize:13, fontWeight:700, color:T.dim1, marginBottom:16 }}>Cost Breakdown</p>
        <div style={{ display:"grid", gridTemplateColumns:"repeat(5,1fr)", gap:14 }}>
          {[
            { label:"Ollama local AI",   value:`$0.00`,              pct:0,  note:"80% of calls",     color:T.green },
            { label:"Retell AI voice",   value:`$${(calls*0.07*0.4).toFixed(2)}`, pct:40, note:"$0.07/min", color:T.teal },
            { label:"Groq fallback",     value:`$${(calls*0.002).toFixed(2)}`, pct:15, note:"15% of calls", color:T.blue },
            { label:"Claude (critical)", value:`$${(calls*0.004).toFixed(2)}`, pct:5,  note:"5% of calls",  color:T.purple },
            { label:"Infrastructure",    value:"$7.40",               pct:100, note:"EC2 + Supabase",  color:T.amber },
          ].map(c => (
            <div key={c.label}>
              <p style={{ fontSize:10, fontWeight:700, color:T.dim3, textTransform:"uppercase", letterSpacing:"0.08em", marginBottom:6 }}>{c.label}</p>
              <p style={{ fontSize:20, fontWeight:900, color:c.color, letterSpacing:"-0.04em" }}>{c.value}</p>
              <p style={{ fontSize:10, color:T.dim3, marginTop:4 }}>{c.note}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
