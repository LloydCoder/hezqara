"use client";
import { useAgents } from "@/hooks/useAgents";
import { useState } from "react";

const CLINIC_ID = process.env.NEXT_PUBLIC_DEMO_CLINIC_ID ?? "demo_clinic";
const T = {
  bg:"#0B1120",surface:"#0F1729",surfaceHi:"#141E35",border:"rgba(255,255,255,0.07)",
  teal:"#00E5CC",tealDim:"rgba(0,229,204,0.12)",tealBorder:"rgba(0,229,204,0.2)",
  amber:"#F5A623",green:"#34D399",purple:"#A78BFA",red:"#FF4D6A",
  white:"#FFFFFF",dim1:"rgba(255,255,255,0.75)",dim2:"rgba(255,255,255,0.45)",
  dim3:"rgba(255,255,255,0.2)",dim4:"rgba(255,255,255,0.06)",
};

const AGENT_DETAILS: Record<string, { desc:string; capabilities:string[]; color:string; icon:string }> = {
  reception:  { color:T.teal,   icon:"◎", desc:"Answers every call in 600ms. Detects intent and routes to specialist agents.", capabilities:["Inbound call answer","Intent detection","Agent routing","Fallback handling"] },
  scheduling: { color:T.purple, icon:"▦", desc:"Fetches live slots, matches patient preferences, books directly into EHR.", capabilities:["Slot availability","Preference matching","EHR write-back","Confirmation SMS"] },
  intake:     { color:"#60A5FA", icon:"◉", desc:"Collects demographics, insurance, and medical history before the visit.", capabilities:["Demographics capture","Insurance collection","Medical history","Pre-visit note draft"] },
  insurance:  { color:T.amber,  icon:"◫", desc:"Real-time eligibility verification and benefits check.", capabilities:["Eligibility check","Copay lookup","Deductible status","Coverage details"] },
  prior_auth: { color:T.red,    icon:"◪", desc:"Submits prior auth via FHIR Da Vinci PAS, polls for decisions automatically.", capabilities:["PA submission","Status polling","Denial management","Appeal support"] },
  refill:     { color:T.green,  icon:"◬", desc:"Parses medication requests, checks eligibility, sends to pharmacy.", capabilities:["Rx parsing","Eligibility check","Pharmacy routing","Provider notification"] },
  records:    { color:"#60A5FA",icon:"◮", desc:"Identity verification and HIPAA-compliant record release.", capabilities:["Identity verify","HIPAA authorization","Record release","Audit logging"] },
  referrals:  { color:T.purple, icon:"◭", desc:"Creates specialist referrals, tracks status end-to-end.", capabilities:["Specialist matching","Referral creation","Status tracking","Patient notification"] },
  recall:     { color:T.amber,  icon:"◩", desc:"Proactive patient outreach via SMS, email, voice, WhatsApp.", capabilities:["Patient selection","Channel selection","Message generation","Response tracking"] },
  email:      { color:T.green,  icon:"◧", desc:"Inbox triage, draft replies, appointment confirmations.", capabilities:["Inbox triage","Draft replies","Confirmations","Follow-ups"] },
};

export default function AgentsPage() {
  const { agents, loading, toggleAgent } = useAgents(CLINIC_ID);
  const [selected, setSelected] = useState<string | null>(null);

  const agentList = agents.length > 0 ? agents
    : Object.entries(AGENT_DETAILS).map(([id]) => ({
        id, name:id, status:"active",
        calls_handled:Math.floor(Math.random()*40+5),
        confidence_score:0.88+Math.random()*0.1,
        avg_handle_time:120+Math.floor(Math.random()*180),
      }));

  const selectedAgent = agentList.find(a => a.id === (selected ?? agentList[0]?.id));
  const detail = AGENT_DETAILS[selectedAgent?.id ?? "reception"] ?? AGENT_DETAILS.reception;

  return (
    <div style={{ minHeight:"100vh", padding:24, background:T.bg, display:"flex", flexDirection:"column", gap:18 }}>
      <div>
        <h1 style={{ fontSize:20, fontWeight:900, color:T.white }}>Agents</h1>
        <p style={{ fontSize:13, color:T.dim3, marginTop:2 }}>Manage all 10 AI agents</p>
      </div>

      <div style={{ display:"grid", gridTemplateColumns:"1fr 340px", gap:16, alignItems:"start" }}>
        {/* Agent grid */}
        <div style={{ display:"grid", gridTemplateColumns:"repeat(2,1fr)", gap:12 }}>
          {loading
            ? Array.from({length:10}).map((_,i) => (
                <div key={i} style={{ height:120, borderRadius:16, background:T.dim4, animation:"pulse 1.5s ease infinite" }} />
              ))
            : agentList.map(agent => {
                const d = AGENT_DETAILS[agent.id] ?? AGENT_DETAILS.reception;
                const isOn   = agent.status !== "disabled";
                const isBusy = agent.status === "busy";
                const isSelected = (selected ?? agentList[0]?.id) === agent.id;
                return (
                  <button key={agent.id}
                    onClick={() => setSelected(agent.id)}
                    style={{
                      background: isSelected ? T.surfaceHi : T.surface,
                      border:`1px solid ${isSelected ? d.color+"40" : T.border}`,
                      borderRadius:16, padding:18, textAlign:"left", cursor:"pointer",
                      transition:"all 0.15s",
                    }}>
                    <div style={{ display:"flex", alignItems:"center", justifyContent:"space-between", marginBottom:12 }}>
                      <div style={{ display:"flex", alignItems:"center", gap:10 }}>
                        <div style={{
                          width:36, height:36, borderRadius:10,
                          display:"flex", alignItems:"center", justifyContent:"center",
                          background:d.color+"18", border:`1px solid ${d.color}30`,
                          fontSize:16, color:d.color,
                        }}>{d.icon}</div>
                        <div>
                          <p style={{ fontSize:13, fontWeight:700, color:T.dim1, textTransform:"capitalize" }}>
                            {agent.id.replace(/_/g," ")}
                          </p>
                          <p style={{ fontSize:10, color: isBusy ? T.amber : isOn ? T.teal : T.dim3 }}>
                            {isBusy ? "On call" : isOn ? "Ready" : "Disabled"}
                          </p>
                        </div>
                      </div>
                      {/* Toggle */}
                      <div onClick={e => { e.stopPropagation(); toggleAgent?.(agent.id, !isOn); }}
                        style={{
                          width:36, height:20, borderRadius:10, cursor:"pointer",
                          background: isOn ? d.color+"30" : T.dim4,
                          border:`1px solid ${isOn ? d.color+"50" : T.border}`,
                          position:"relative", transition:"all 0.2s",
                        }}>
                        <div style={{
                          position:"absolute", top:2,
                          left: isOn ? 18 : 2,
                          width:16, height:16, borderRadius:8,
                          background: isOn ? d.color : T.dim3,
                          transition:"left 0.2s",
                          boxShadow: isOn ? `0 0 8px ${d.color}` : "none",
                        }} />
                      </div>
                    </div>
                    <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr 1fr", gap:8 }}>
                      {[
                        { l:"Calls",       v:agent.calls_handled ?? "—" },
                        { l:"Confidence",  v:agent.confidence_score ? `${(agent.confidence_score*100).toFixed(0)}%` : "—" },
                        { l:"Avg time",    v:agent.avg_handle_time ? `${Math.round(agent.avg_handle_time/60)}m` : "—" },
                      ].map(m => (
                        <div key={m.l}>
                          <p style={{ fontSize:9, color:T.dim3, textTransform:"uppercase", letterSpacing:"0.08em" }}>{m.l}</p>
                          <p style={{ fontSize:15, fontWeight:800, color:d.color, letterSpacing:"-0.02em" }}>{m.v}</p>
                        </div>
                      ))}
                    </div>
                  </button>
                );
              })
          }
        </div>

        {/* Detail panel */}
        {selectedAgent && (
          <div style={{ background:T.surface, border:`1px solid ${detail.color}30`, borderRadius:18, padding:24, position:"sticky", top:24 }}>
            <div style={{ display:"flex", alignItems:"center", gap:12, marginBottom:20 }}>
              <div style={{
                width:44, height:44, borderRadius:12,
                display:"flex", alignItems:"center", justifyContent:"center",
                background:detail.color+"18", border:`1px solid ${detail.color}30`,
                fontSize:22, color:detail.color,
              }}>{detail.icon}</div>
              <div>
                <p style={{ fontSize:15, fontWeight:800, color:T.dim1, textTransform:"capitalize" }}>
                  {selectedAgent.id.replace(/_/g," ")} Agent
                </p>
                <p style={{ fontSize:11, color: selectedAgent.status==="busy" ? T.amber : T.teal }}>
                  {selectedAgent.status==="busy" ? "Currently on call" : selectedAgent.status==="disabled" ? "Disabled" : "Ready"}
                </p>
              </div>
            </div>
            <p style={{ fontSize:13, color:T.dim2, lineHeight:1.6, marginBottom:20 }}>{detail.desc}</p>
            <p style={{ fontSize:10, fontWeight:700, letterSpacing:"0.1em", textTransform:"uppercase", color:T.dim3, marginBottom:10 }}>Capabilities</p>
            <div style={{ display:"flex", flexDirection:"column", gap:6 }}>
              {detail.capabilities.map(cap => (
                <div key={cap} style={{ display:"flex", alignItems:"center", gap:8 }}>
                  <div style={{ width:5, height:5, borderRadius:"50%", background:detail.color, flexShrink:0 }} />
                  <span style={{ fontSize:12, color:T.dim2 }}>{cap}</span>
                </div>
              ))}
            </div>
            <div style={{ marginTop:20, paddingTop:16, borderTop:`1px solid ${T.border}`,
                          display:"grid", gridTemplateColumns:"1fr 1fr", gap:12 }}>
              {[
                { l:"Calls today",  v:selectedAgent.calls_handled ?? 0, color:detail.color },
                { l:"Confidence",   v:selectedAgent.confidence_score ? `${(selectedAgent.confidence_score*100).toFixed(0)}%` : "—", color:T.green },
                { l:"Avg duration", v:selectedAgent.avg_handle_time ? `${Math.round(selectedAgent.avg_handle_time/60)}m` : "—", color:T.amber },
                { l:"Success rate", v:"97%", color:T.purple },
              ].map(m => (
                <div key={m.l} style={{ background:T.dim4, borderRadius:10, padding:12 }}>
                  <p style={{ fontSize:9, color:T.dim3, textTransform:"uppercase", letterSpacing:"0.08em", marginBottom:4 }}>{m.l}</p>
                  <p style={{ fontSize:20, fontWeight:900, color:m.color, letterSpacing:"-0.03em" }}>{m.v}</p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
