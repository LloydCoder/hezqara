"use client";
import { useState } from "react";

const T = {
  bg:"#0B1120",surface:"#0F1729",border:"rgba(255,255,255,0.07)",
  teal:"#00E5CC",tealDim:"rgba(0,229,204,0.12)",tealBorder:"rgba(0,229,204,0.2)",
  amber:"#F5A623",green:"#34D399",red:"#FF4D6A",purple:"#A78BFA",
  white:"#FFFFFF",dim1:"rgba(255,255,255,0.75)",dim2:"rgba(255,255,255,0.45)",
  dim3:"rgba(255,255,255,0.2)",dim4:"rgba(255,255,255,0.06)",
};

const HIPAA_CHECKS = [
  { label:"HIPAA BAA — Retell AI (voice)",     status:"pass",    detail:"Signed at platform level",               category:"BAA" },
  { label:"HIPAA BAA — Supabase (database)",   status:"pass",    detail:"Frankfurt region, EU adequacy",          category:"BAA" },
  { label:"PHI Audit Log Active",              status:"pass",    detail:"Every PHI access recorded, immutable",   category:"Technical" },
  { label:"Row-Level Security (RLS)",          status:"pass",    detail:"All 13 tables — zero cross-tenant access",category:"Technical" },
  { label:"Data at Rest Encrypted",            status:"pass",    detail:"AES-256 via Supabase managed",           category:"Technical" },
  { label:"Data in Transit Encrypted",         status:"pass",    detail:"TLS 1.3 enforced at nginx layer",        category:"Technical" },
  { label:"Phone Numbers Masked in Logs",      status:"pass",    detail:"+1212555**** — PHI never in logs",       category:"Technical" },
  { label:"AI Shield — Injection Protection",  status:"pass",    detail:"Parliament Ensemble, 11 attack patterns",category:"Technical" },
  { label:"Minimum Necessary Access (RBAC)",   status:"pass",    detail:"Clerk org-scoped roles — admin/member",  category:"Administrative" },
  { label:"Breach Notification Policy",        status:"pass",    detail:"72-hour window documented",              category:"Administrative" },
  { label:"Annual Risk Assessment",            status:"pending", detail:"BugFlow Elite scan — schedule Q3",       category:"Administrative" },
  { label:"HIPAA Staff Training",              status:"pending", detail:"Required before first patient goes live",category:"Administrative" },
  { label:"Penetration Testing",               status:"pending", detail:"BugFlow Elite — Q3 2026",                category:"Technical" },
];

const NDPR_CHECKS = [
  { label:"NDPR Lawful Basis Documented",      status:"pass",    detail:"Consent + legitimate interest" },
  { label:"Data Processing Agreement (DPA)",   status:"pass",    detail:"NDPR-compliant DPA template ready" },
  { label:"4-Language Patient Notices",        status:"pass",    detail:"English, Igbo, Yoruba, Hausa" },
  { label:"Data Subject Rights Workflow",      status:"pass",    detail:"Access, deletion, portability" },
  { label:"NITDA Registration",                status:"pending", detail:"Apply when first Nigerian clinic signs" },
];

const AUDIT_LOG = [
  { id:1, event:"PHI_ACCESS",     actor:"Scheduling Agent",  resource:"Patient/PAT-001", time:"09:14:23", ip:"13.50.16.19" },
  { id:2, event:"APPOINTMENT_CREATE", actor:"Scheduling Agent", resource:"APT-0892",    time:"09:14:31", ip:"13.50.16.19" },
  { id:3, event:"EHR_READ",       actor:"Insurance Agent",   resource:"Patient/PAT-001", time:"09:08:12", ip:"13.50.16.19" },
  { id:4, event:"CALL_RECORDED",  actor:"Reception Agent",   resource:"CALL-2831",       time:"08:55:44", ip:"13.50.16.19" },
  { id:5, event:"PHI_ACCESS",     actor:"Intake Agent",      resource:"Patient/PAT-004", time:"08:41:09", ip:"13.50.16.19" },
];

const STATUS_CONFIG = {
  pass:    { color:T.green,  bg:"rgba(52,211,153,0.12)", border:"rgba(52,211,153,0.25)", icon:"✓" },
  pending: { color:T.amber,  bg:"rgba(245,166,35,0.12)", border:"rgba(245,166,35,0.25)", icon:"○" },
  fail:    { color:T.red,    bg:"rgba(255,77,106,0.12)", border:"rgba(255,77,106,0.25)", icon:"✗" },
};

export default function CompliancePage() {
  const [tab, setTab] = useState<"hipaa"|"ndpr"|"audit">("hipaa");
  const passCount = HIPAA_CHECKS.filter(c=>c.status==="pass").length;
  const score = Math.round((passCount/HIPAA_CHECKS.length)*100);

  return (
    <div style={{ minHeight:"100vh", padding:24, background:T.bg, display:"flex", flexDirection:"column", gap:18 }}>
      <div style={{ display:"flex", alignItems:"center", justifyContent:"space-between" }}>
        <div>
          <h1 style={{ fontSize:20, fontWeight:900, color:T.white }}>Compliance</h1>
          <p style={{ fontSize:13, color:T.dim3, marginTop:2 }}>HIPAA · NDPR · Audit trail</p>
        </div>
        {/* Score */}
        <div style={{ display:"flex", alignItems:"center", gap:16 }}>
          <div style={{ textAlign:"right" }}>
            <p style={{ fontSize:11, color:T.dim3 }}>HIPAA Score</p>
            <p style={{ fontSize:32, fontWeight:900, color: score>=80 ? T.green : T.amber,
                        letterSpacing:"-0.04em", lineHeight:1 }}>{score}%</p>
          </div>
          <div style={{
            width:56, height:56, borderRadius:"50%",
            border:`3px solid ${score>=80 ? T.green : T.amber}`,
            display:"flex", alignItems:"center", justifyContent:"center",
            boxShadow:`0 0 20px ${score>=80 ? T.green : T.amber}40`,
          }}>
            <span style={{ fontSize:20 }}>{score>=80 ? "✓" : "!"}</span>
          </div>
        </div>
      </div>

      {/* Summary cards */}
      <div style={{ display:"grid", gridTemplateColumns:"repeat(4,1fr)", gap:14 }}>
        {[
          { label:"Checks passing", value:`${passCount}/${HIPAA_CHECKS.length}`, color:T.green },
          { label:"Pending actions", value:HIPAA_CHECKS.filter(c=>c.status==="pending").length, color:T.amber },
          { label:"BAAs signed",    value:"2 / 2", color:T.teal },
          { label:"Audit events",   value:"4,891", color:T.purple },
        ].map(s => (
          <div key={s.label} style={{ background:T.surface, border:`1px solid ${T.border}`, borderRadius:14, padding:18 }}>
            <p style={{ fontSize:10, fontWeight:700, letterSpacing:"0.1em", textTransform:"uppercase", color:T.dim3 }}>{s.label}</p>
            <p style={{ fontSize:28, fontWeight:900, color:s.color, marginTop:6, letterSpacing:"-0.04em" }}>{s.value}</p>
          </div>
        ))}
      </div>

      {/* Tab switcher */}
      <div style={{ display:"flex", gap:2, background:T.surface, border:`1px solid ${T.border}`, borderRadius:12, padding:4, alignSelf:"flex-start" }}>
        {[["hipaa","HIPAA (US)"],["ndpr","NDPR (Nigeria)"],["audit","Audit Log"]].map(([id,label]) => (
          <button key={id} onClick={() => setTab(id as any)}
            style={{
              padding:"7px 18px", borderRadius:9, fontSize:12, fontWeight:600,
              cursor:"pointer", border:"none",
              background: tab===id ? T.tealDim : "transparent",
              color:      tab===id ? T.teal    : T.dim3,
            }}>{label}</button>
        ))}
      </div>

      {/* HIPAA checks */}
      {tab === "hipaa" && (
        <div style={{ background:T.surface, border:`1px solid ${T.border}`, borderRadius:18, overflow:"hidden" }}>
          {HIPAA_CHECKS.map((check, i) => {
            const cfg = STATUS_CONFIG[check.status as keyof typeof STATUS_CONFIG];
            return (
              <div key={i} style={{
                display:"flex", alignItems:"center", gap:14, padding:"14px 20px",
                borderBottom: i < HIPAA_CHECKS.length-1 ? `1px solid ${T.border}` : "none",
              }}>
                <div style={{
                  width:28, height:28, borderRadius:8, flexShrink:0,
                  display:"flex", alignItems:"center", justifyContent:"center",
                  background:cfg.bg, border:`1px solid ${cfg.border}`,
                  fontSize:13, color:cfg.color, fontWeight:700,
                }}>{cfg.icon}</div>
                <div style={{ flex:1 }}>
                  <p style={{ fontSize:13, fontWeight:600, color:T.dim1 }}>{check.label}</p>
                  <p style={{ fontSize:11, color:T.dim3, marginTop:2 }}>{check.detail}</p>
                </div>
                <span style={{ fontSize:10, fontWeight:700, padding:"3px 10px", borderRadius:100,
                               background:cfg.bg, color:cfg.color, border:`1px solid ${cfg.border}` }}>
                  {check.category}
                </span>
              </div>
            );
          })}
        </div>
      )}

      {/* NDPR checks */}
      {tab === "ndpr" && (
        <div style={{ background:T.surface, border:`1px solid ${T.border}`, borderRadius:18, overflow:"hidden" }}>
          {NDPR_CHECKS.map((check, i) => {
            const cfg = STATUS_CONFIG[check.status as keyof typeof STATUS_CONFIG];
            return (
              <div key={i} style={{
                display:"flex", alignItems:"center", gap:14, padding:"14px 20px",
                borderBottom: i < NDPR_CHECKS.length-1 ? `1px solid ${T.border}` : "none",
              }}>
                <div style={{
                  width:28, height:28, borderRadius:8, flexShrink:0,
                  display:"flex", alignItems:"center", justifyContent:"center",
                  background:cfg.bg, border:`1px solid ${cfg.border}`,
                  fontSize:13, color:cfg.color, fontWeight:700,
                }}>{cfg.icon}</div>
                <div style={{ flex:1 }}>
                  <p style={{ fontSize:13, fontWeight:600, color:T.dim1 }}>{check.label}</p>
                  <p style={{ fontSize:11, color:T.dim3, marginTop:2 }}>{check.detail}</p>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Audit log */}
      {tab === "audit" && (
        <div style={{ background:T.surface, border:`1px solid ${T.border}`, borderRadius:18, overflow:"hidden" }}>
          <table style={{ width:"100%", borderCollapse:"collapse" }}>
            <thead>
              <tr style={{ borderBottom:`1px solid ${T.border}` }}>
                {["Event","Actor","Resource","Time","IP"].map(h => (
                  <th key={h} style={{ textAlign:"left", padding:"12px 20px", fontSize:10,
                                       fontWeight:700, letterSpacing:"0.1em",
                                       textTransform:"uppercase", color:T.dim3 }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {AUDIT_LOG.map((log, i) => (
                <tr key={log.id} style={{ borderBottom: i < AUDIT_LOG.length-1 ? `1px solid ${T.border}` : "none" }}>
                  <td style={{ padding:"12px 20px" }}>
                    <span style={{
                      fontSize:11, fontWeight:600, padding:"3px 8px", borderRadius:6,
                      background: log.event.includes("PHI") ? "rgba(245,166,35,0.12)" : T.tealDim,
                      color: log.event.includes("PHI") ? T.amber : T.teal,
                    }}>{log.event}</span>
                  </td>
                  <td style={{ padding:"12px 20px", fontSize:12, color:T.dim2 }}>{log.actor}</td>
                  <td style={{ padding:"12px 20px", fontSize:12, fontFamily:"monospace", color:T.dim2 }}>{log.resource}</td>
                  <td style={{ padding:"12px 20px", fontSize:12, fontFamily:"monospace", color:T.dim3 }}>{log.time}</td>
                  <td style={{ padding:"12px 20px", fontSize:12, fontFamily:"monospace", color:T.dim3 }}>{log.ip}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
