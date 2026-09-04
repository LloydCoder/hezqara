import { useState, useEffect, useRef } from "react";

const T = {
  bg:         "#0B1120",
  surface:    "#0F1729",
  surfaceHi:  "#141E35",
  border:     "rgba(255,255,255,0.07)",
  teal:       "#00E5CC",
  tealDim:    "rgba(0,229,204,0.12)",
  tealBorder: "rgba(0,229,204,0.2)",
  amber:      "#F5A623",
  amberDim:   "rgba(245,166,35,0.12)",
  red:        "#FF4D6A",
  green:      "#34D399",
  purple:     "#A78BFA",
  blue:       "#60A5FA",
  white:      "#FFFFFF",
  dim1:       "rgba(255,255,255,0.75)",
  dim2:       "rgba(255,255,255,0.45)",
  dim3:       "rgba(255,255,255,0.2)",
  dim4:       "rgba(255,255,255,0.06)",
};

const NAV = [
  { id:"dashboard",    label:"Command",   icon:"⚡", group:"main" },
  { id:"agents",       label:"Agents",    icon:"◈",  group:"main" },
  { id:"calls",        label:"Calls",     icon:"◎",  group:"main" },
  { id:"appointments", label:"Schedule",  icon:"▦",  group:"main" },
  { id:"patients",     label:"Patients",  icon:"◉",  group:"main" },
  { id:"insurance",    label:"Insurance", icon:"◫",  group:"clinical" },
  { id:"prior_auth",   label:"Prior Auth",icon:"◪",  group:"clinical" },
  { id:"recalls",      label:"Recalls",   icon:"◬",  group:"clinical" },
  { id:"analytics",    label:"Analytics", icon:"◩",  group:"ops" },
  { id:"compliance",   label:"Compliance",icon:"◈",  group:"ops" },
  { id:"settings",     label:"Settings",  icon:"◧",  group:"ops" },
];

const GROUPS = [
  { id:"main",     label:"OPERATIONS" },
  { id:"clinical", label:"CLINICAL"   },
  { id:"ops",      label:"INSIGHTS"   },
];

const AGENTS = [
  { id:"reception",  label:"Reception",  busy:true  },
  { id:"scheduling", label:"Schedule",   busy:false },
  { id:"intake",     label:"Intake",     busy:false },
  { id:"insurance",  label:"Insurance",  busy:true  },
  { id:"prior_auth", label:"Prior Auth", busy:false },
  { id:"refill",     label:"Refill",     busy:false },
  { id:"records",    label:"Records",    busy:false },
  { id:"referrals",  label:"Referrals",  busy:false },
  { id:"recall",     label:"Recall",     busy:false },
  { id:"email",      label:"Email",      busy:false },
];

const DEMO_CALLS = [
  { id:1, name:"Maria Santos",   intent:"scheduling", outcome:"booked",    time:"09:14", dur:"3m 07s" },
  { id:2, name:"James Mitchell", intent:"refill",     outcome:"resolved",  time:"09:08", dur:"2m 41s" },
  { id:3, name:"Priya Sharma",   intent:"insurance",  outcome:"resolved",  time:"08:55", dur:"4m 18s" },
  { id:4, name:"Amaka Obi",      intent:"scheduling", outcome:"booked",    time:"08:41", dur:"2m 55s" },
  { id:5, name:"Robert Chen",    intent:"records",    outcome:"resolved",  time:"08:30", dur:"1m 48s" },
];

const INTENT_COLOR = {
  scheduling: T.teal,
  insurance:  T.purple,
  refill:     T.amber,
  records:    T.blue,
  referral:   T.green,
};

// ── Waveform canvas ────────────────────────────────────────────────────────
function Waveform({ active }) {
  const canvasRef = useRef(null);
  const animRef   = useRef(0);
  const phaseRef  = useRef(0);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    const W = canvas.width, H = canvas.height;

    const draw = () => {
      ctx.clearRect(0, 0, W, H);
      const amp   = active ? 14 : 2.5;
      const freq  = active ? 0.09 : 0.035;
      phaseRef.current += active ? 0.11 : 0.018;

      ctx.beginPath();
      ctx.strokeStyle = active ? T.teal : "rgba(0,229,204,0.22)";
      ctx.lineWidth = 1.5;
      ctx.shadowBlur = active ? 10 : 0;
      ctx.shadowColor = T.teal;

      for (let x = 0; x < W; x++) {
        const y = H/2
          + amp * Math.sin(freq * x + phaseRef.current)
          + (active ? amp * 0.35 * Math.sin(freq * 2.4 * x + phaseRef.current * 1.6) : 0);
        x === 0 ? ctx.moveTo(x,y) : ctx.lineTo(x,y);
      }
      ctx.stroke();
      animRef.current = requestAnimationFrame(draw);
    };
    draw();
    return () => cancelAnimationFrame(animRef.current);
  }, [active]);

  return <canvas ref={canvasRef} width={160} height={36} style={{ display:"block" }} />;
}

// ── Stat card ──────────────────────────────────────────────────────────────
function StatCard({ label, value, sub, color }) {
  return (
    <div style={{ background:T.surface, border:`1px solid ${T.border}`,
                  borderRadius:16, padding:"20px 20px 16px" }}>
      <p style={{ fontSize:10, fontWeight:700, letterSpacing:"0.1em",
                  textTransform:"uppercase", color:T.dim3, marginBottom:8 }}>{label}</p>
      <p style={{ fontSize:32, fontWeight:900, letterSpacing:"-0.04em",
                  lineHeight:1, color:color,
                  textShadow:`0 0 24px ${color}50` }}>{value}</p>
      {sub && <p style={{ fontSize:11, color:T.dim3, marginTop:6 }}>{sub}</p>}
    </div>
  );
}

// ── Agent pill ─────────────────────────────────────────────────────────────
function AgentPill({ agent, on, onClick }) {
  const isBusy = agent.busy && on;
  const borderColor = on ? (isBusy ? T.amber+"50" : T.tealBorder) : T.border;
  const textColor   = on ? (isBusy ? T.amber      : T.teal)       : T.dim3;
  return (
    <button onClick={onClick}
      style={{
        background: on ? T.surfaceHi : T.dim4,
        border:`1px solid ${borderColor}`,
        borderRadius:12, padding:"10px 12px",
        display:"flex", alignItems:"center", gap:10,
        cursor:"pointer", transition:"all 0.15s", width:"100%", textAlign:"left",
      }}>
      <div style={{ width:8, height:8, borderRadius:"50%", flexShrink:0,
                    background: on ? (isBusy ? T.amber : T.teal) : T.dim3,
                    boxShadow: on ? `0 0 8px ${isBusy ? T.amber : T.teal}` : "none" }} />
      <div style={{ minWidth:0 }}>
        <p style={{ fontSize:12, fontWeight:600, color:T.dim1,
                    whiteSpace:"nowrap", overflow:"hidden", textOverflow:"ellipsis" }}>
          {agent.label}
        </p>
        <p style={{ fontSize:10, color:textColor }}>
          {isBusy ? "On call" : on ? "Ready" : "Off"}
        </p>
      </div>
    </button>
  );
}

// ── Settings panel ─────────────────────────────────────────────────────────
function SettingsPanel() {
  const [ehr, setEhr] = useState("athenahealth");
  const [clientId, setClientId] = useState("");
  const [clientSecret, setClientSecret] = useState("");
  const [connStatus, setConnStatus] = useState("idle");
  const isStandalone = ehr === "standalone";

  const test = async () => {
    setConnStatus("testing");
    await new Promise(r => setTimeout(r, 1800));
    setConnStatus(clientId ? "ok" : "fail");
  };

  const inputStyle = {
    background: T.dim4, border:`1px solid ${T.border}`,
    borderRadius:10, padding:"10px 14px",
    color:T.dim1, fontSize:13, outline:"none", width:"100%",
  };
  const labelStyle = {
    fontSize:10, fontWeight:700, letterSpacing:"0.1em",
    textTransform:"uppercase", color:T.dim3, display:"block", marginBottom:6,
  };

  return (
    <div style={{ display:"flex", flexDirection:"column", gap:16 }}>
      {/* Clinic info */}
      <div style={{ background:T.surface, border:`1px solid ${T.border}`, borderRadius:16, padding:20 }}>
        <p style={{ fontSize:13, fontWeight:700, color:T.dim1, marginBottom:16 }}>Clinic Details</p>
        <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:12 }}>
          {[["Clinic name","Family Care Associates"],["Country","US"],
            ["Phone","+1 (888) 555-0001"],["Timezone","America/New_York"]].map(([l,v]) => (
            <div key={l}>
              <label style={labelStyle}>{l}</label>
              <input style={inputStyle} defaultValue={v} />
            </div>
          ))}
        </div>
      </div>

      {/* EHR connection */}
      <div style={{ background:T.surface, border:`1px solid ${T.border}`, borderRadius:16, padding:20 }}>
        <p style={{ fontSize:13, fontWeight:700, color:T.dim1, marginBottom:16 }}>EHR Connection</p>
        <div style={{ marginBottom:12 }}>
          <label style={labelStyle}>EHR System</label>
          <select value={ehr} onChange={e => { setEhr(e.target.value); setConnStatus("idle"); }}
            style={{ ...inputStyle, cursor:"pointer" }}>
            <option value="standalone">Standalone (No EHR) — Global</option>
            <option value="athenahealth">athenahealth — US</option>
            <option value="modmed">ModMed EMA — Specialty</option>
            <option value="epic">Epic SMART on FHIR — Enterprise</option>
            <option value="eclinicalworks">eClinicalWorks — US</option>
            <option value="nextgen">NextGen — US</option>
            <option value="drchrono">DrChrono — US</option>
            <option value="elation">Elation Health — US</option>
            <option value="helium_health">Helium Health — Nigeria</option>
            <option value="cerner">Cerner (Oracle Health) — Enterprise</option>
            <option value="openmrs">OpenMRS — Africa / Global</option>
          </select>
        </div>

        {isStandalone ? (
          <div style={{ background:T.tealDim, border:`1px solid ${T.tealBorder}`,
                        borderRadius:12, padding:"14px 16px", display:"flex", gap:12 }}>
            <span style={{ color:T.teal, fontSize:18, flexShrink:0 }}>◈</span>
            <div>
              <p style={{ fontSize:13, fontWeight:600, color:T.teal, marginBottom:4 }}>
                Standalone Mode Active
              </p>
              <p style={{ fontSize:12, color:T.dim2, lineHeight:1.5 }}>
                Carenova stores all patient records directly. No EHR required.
                Works globally — perfect for paper-based clinics.
                Connect an EHR anytime without losing data.
              </p>
            </div>
          </div>
        ) : (
          <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:12 }}>
            <div>
              <label style={labelStyle}>Client ID</label>
              <input style={inputStyle} value={clientId}
                onChange={e => setClientId(e.target.value)} placeholder="Client ID" />
            </div>
            <div>
              <label style={labelStyle}>Client Secret</label>
              <input style={{ ...inputStyle }} type="password"
                value={clientSecret} onChange={e => setClientSecret(e.target.value)}
                placeholder="••••••••••" />
            </div>
            <div>
              <label style={labelStyle}>Practice ID</label>
              <input style={inputStyle} placeholder="Practice / Org ID" />
            </div>
          </div>
        )}

        {!isStandalone && (
          <div style={{ display:"flex", alignItems:"center", gap:12, marginTop:12 }}>
            <button onClick={test}
              style={{
                background: T.tealDim, border:`1px solid ${T.tealBorder}`,
                borderRadius:10, padding:"9px 20px",
                color: T.teal, fontSize:13, fontWeight:600, cursor:"pointer",
              }}>
              {connStatus === "testing" ? "Testing…" : "Test Connection"}
            </button>
            {connStatus === "ok" &&
              <span style={{ color:T.green, fontSize:13, fontWeight:600 }}>✓ Connected</span>}
            {connStatus === "fail" &&
              <span style={{ color:T.red, fontSize:13, fontWeight:600 }}>✗ Check credentials</span>}
          </div>
        )}
      </div>

      <div style={{ display:"flex", justifyContent:"flex-end" }}>
        <button style={{
          background:"linear-gradient(135deg, #00E5CC, #0099BB)",
          border:"none", borderRadius:12, padding:"11px 28px",
          color:"#070C17", fontSize:13, fontWeight:700, cursor:"pointer",
        }}>
          Save Changes
        </button>
      </div>
    </div>
  );
}

// ── Main app ───────────────────────────────────────────────────────────────
export default function CarenovaDashboard() {
  const [page, setPage]           = useState("dashboard");
  const [activeCall, setActiveCall] = useState(false);
  const [agentStates, setAgentStates] = useState(
    Object.fromEntries(AGENTS.map(a => [a.id, true]))
  );
  const [callCount, setCallCount] = useState(23);
  const [savings,   setSavings]   = useState(221.03);

  useEffect(() => {
    const t = setInterval(() => {
      setActiveCall(p => !p);
      if (Math.random() > 0.6) {
        setCallCount(c => c + 1);
        setSavings(s => +(s + 9.61).toFixed(2));
      }
    }, 3200);
    return () => clearInterval(t);
  }, []);

  const toggleAgent = (id) =>
    setAgentStates(s => ({ ...s, [id]: !s[id] }));

  // ── Sidebar ──
  const Sidebar = () => (
    <div style={{
      position:"fixed", inset:"0 auto 0 0", width:224, zIndex:50,
      background:"#070C17", borderRight:`1px solid ${T.border}`,
      display:"flex", flexDirection:"column",
    }}>
      {/* Logo */}
      <div style={{ padding:"18px 20px 16px", borderBottom:`1px solid ${T.border}` }}>
        <div style={{ display:"flex", alignItems:"center", gap:10 }}>
          <div style={{
            width:32, height:32, borderRadius:9, display:"flex",
            alignItems:"center", justifyContent:"center",
            background:"linear-gradient(135deg, #00E5CC, #0099BB)",
            fontWeight:900, fontSize:14, color:"#070C17",
          }}>C</div>
          <div>
            <p style={{ fontSize:13, fontWeight:800, color:T.white, letterSpacing:"-0.01em" }}>
              Carenova
            </p>
            <p style={{ fontSize:10, color:T.dim3 }}>AI Front Office</p>
          </div>
        </div>
      </div>

      {/* Nav */}
      <nav style={{ flex:1, overflowY:"auto", padding:"14px 10px", display:"flex", flexDirection:"column", gap:18 }}>
        {GROUPS.map(g => (
          <div key={g.id}>
            <p style={{ fontSize:10, fontWeight:700, letterSpacing:"0.12em",
                        textTransform:"uppercase", color:T.dim3,
                        padding:"0 8px", marginBottom:4 }}>{g.label}</p>
            {NAV.filter(n => n.group === g.id).map(n => {
              const active = n.id === page;
              return (
                <button key={n.id} onClick={() => setPage(n.id)}
                  style={{
                    display:"flex", alignItems:"center", gap:9,
                    width:"100%", padding:"8px 10px", borderRadius:10,
                    background: active ? "rgba(0,229,204,0.1)" : "transparent",
                    border: "none",
                    color: active ? T.teal : T.dim3,
                    cursor:"pointer", transition:"all 0.12s",
                    textAlign:"left", marginBottom:1,
                  }}>
                  <span style={{ fontSize:12, width:16, textAlign:"center" }}>{n.icon}</span>
                  <span style={{ fontSize:13, fontWeight: active ? 600 : 400 }}>{n.label}</span>
                  {active && <div style={{ marginLeft:"auto", width:6, height:6, borderRadius:"50%",
                                           background:T.teal, boxShadow:`0 0 8px ${T.teal}` }} />}
                </button>
              );
            })}
          </div>
        ))}
      </nav>

      {/* Live pill */}
      <div style={{ padding:"0 12px 14px" }}>
        <div style={{
          borderRadius:10, padding:"9px 12px",
          background:T.tealDim, border:`1px solid ${T.tealBorder}`,
          display:"flex", alignItems:"center", gap:8,
        }}>
          <span style={{ position:"relative", display:"inline-flex", width:8, height:8 }}>
            <span style={{
              position:"absolute", inset:0, borderRadius:"50%",
              background:T.teal, opacity:0.7,
              animation:"ping 1.4s cubic-bezier(0,0,0.2,1) infinite",
            }} />
            <span style={{ position:"relative", width:8, height:8, borderRadius:"50%", background:T.teal }} />
          </span>
          <span style={{ fontSize:11, fontWeight:600, color:T.teal }}>System Live</span>
          <span style={{ marginLeft:"auto", fontSize:10, color:T.dim3 }}>HIPAA ✓</span>
        </div>
      </div>
    </div>
  );

  // ── Command centre ──
  const CommandCentre = () => (
    <div style={{ display:"flex", flexDirection:"column", gap:18 }}>
      {/* Header */}
      <div style={{ display:"flex", alignItems:"flex-start", justifyContent:"space-between" }}>
        <div>
          <h1 style={{ fontSize:20, fontWeight:900, color:T.white, letterSpacing:"-0.02em" }}>
            Command Centre
          </h1>
          <p style={{ fontSize:13, color:T.dim3, marginTop:2 }}>
            Live overview · all AI agents and clinic activity
          </p>
        </div>
        {/* Waveform status */}
        <div style={{
          background:T.surface, border:`1px solid ${T.border}`,
          borderRadius:14, padding:"10px 16px", display:"flex", alignItems:"center", gap:14,
        }}>
          <div>
            <p style={{ fontSize:10, fontWeight:700, letterSpacing:"0.1em",
                        color: activeCall ? T.teal : T.dim3, marginBottom:6 }}>
              {activeCall ? "● LIVE CALL" : "○ STANDBY"}
            </p>
            <Waveform active={activeCall} />
          </div>
          <div style={{ borderLeft:`1px solid ${T.border}`, paddingLeft:14 }}>
            <p style={{ fontSize:10, color:T.dim3 }}>TODAY</p>
            <p style={{ fontSize:14, fontWeight:700, color:T.dim1 }}>
              {new Date().toLocaleDateString("en-US",{ month:"short", day:"numeric" })}
            </p>
          </div>
        </div>
      </div>

      {/* Savings banner */}
      <div style={{
        borderRadius:18, padding:"18px 24px",
        background:"linear-gradient(135deg, rgba(0,229,204,0.1) 0%, rgba(0,153,187,0.06) 100%)",
        border:`1px solid ${T.tealBorder}`,
        display:"flex", alignItems:"center", justifyContent:"space-between",
      }}>
        <div>
          <p style={{ fontSize:10, fontWeight:700, letterSpacing:"0.1em",
                      textTransform:"uppercase", color:T.teal, marginBottom:6 }}>
            Cost savings today
          </p>
          <p style={{ fontSize:40, fontWeight:900, letterSpacing:"-0.04em", color:T.white, lineHeight:1 }}>
            ${savings.toFixed(2)}
          </p>
          <p style={{ fontSize:11, color:T.dim3, marginTop:6 }}>
            vs. $103/day for a human receptionist
          </p>
        </div>
        <div style={{ textAlign:"right", display:"flex", flexDirection:"column", gap:6 }}>
          <div style={{ display:"flex", alignItems:"center", gap:10, justifyContent:"flex-end" }}>
            <span style={{ fontSize:12, color:T.dim3 }}>Receptionist</span>
            <span style={{ fontSize:18, fontWeight:700,
                           textDecoration:"line-through", color:"rgba(255,77,106,0.7)" }}>$103/day</span>
          </div>
          <div style={{ display:"flex", alignItems:"center", gap:10, justifyContent:"flex-end" }}>
            <span style={{ fontSize:12, color:T.dim3 }}>Carenova</span>
            <span style={{ fontSize:18, fontWeight:700, color:T.teal }}>$7.40/day</span>
          </div>
        </div>
      </div>

      {/* 4 stats */}
      <div style={{ display:"grid", gridTemplateColumns:"repeat(4,1fr)", gap:14 }}>
        <StatCard label="Calls handled"        value={callCount} sub="by AI today"          color={T.teal}   />
        <StatCard label="Appointments booked"  value={Math.floor(callCount*0.73)} sub="written to EHR" color={T.purple} />
        <StatCard label="Hours saved"          value={`${(callCount*0.07).toFixed(1)}h`} sub="receptionist freed" color={T.amber} />
        <StatCard label="Revenue recovered"    value={`$${(savings*3.2).toFixed(0)}`} sub="recalls + prior auths" color={T.green} />
      </div>

      {/* Bento: agents + calls */}
      <div style={{ display:"grid", gridTemplateColumns:"2fr 1fr", gap:14 }}>
        {/* Agents */}
        <div style={{ background:T.surface, border:`1px solid ${T.border}`, borderRadius:18, padding:20 }}>
          <div style={{ display:"flex", alignItems:"center", justifyContent:"space-between", marginBottom:16 }}>
            <div>
              <p style={{ fontSize:13, fontWeight:700, color:T.dim1 }}>Active Agents</p>
              <p style={{ fontSize:11, color:T.dim3 }}>
                {Object.values(agentStates).filter(Boolean).length} of {AGENTS.length} online
              </p>
            </div>
            <span style={{
              fontSize:10, fontWeight:700, padding:"4px 10px", borderRadius:100,
              background:T.tealDim, color:T.teal, border:`1px solid ${T.tealBorder}`,
            }}>AI LIVE</span>
          </div>
          <div style={{ display:"grid", gridTemplateColumns:"repeat(5,1fr)", gap:8 }}>
            {AGENTS.map(a => (
              <AgentPill key={a.id} agent={a}
                on={agentStates[a.id]}
                onClick={() => toggleAgent(a.id)} />
            ))}
          </div>
        </div>

        {/* Call feed */}
        <div style={{ background:T.surface, border:`1px solid ${T.border}`, borderRadius:18, padding:20,
                      display:"flex", flexDirection:"column" }}>
          <div style={{ display:"flex", alignItems:"center", justifyContent:"space-between", marginBottom:14 }}>
            <p style={{ fontSize:13, fontWeight:700, color:T.dim1 }}>Live Calls</p>
            <span style={{ position:"relative", display:"inline-flex", width:8, height:8 }}>
              <span style={{
                position:"absolute", inset:0, borderRadius:"50%", background:T.teal,
                opacity:0.7, animation:"ping 1.4s cubic-bezier(0,0,0.2,1) infinite",
              }} />
              <span style={{ position:"relative", width:8, height:8, borderRadius:"50%", background:T.teal }} />
            </span>
          </div>
          <div style={{ flex:1, display:"flex", flexDirection:"column", gap:0 }}>
            {DEMO_CALLS.map((call, i) => {
              const c = INTENT_COLOR[call.intent] ?? T.dim3;
              return (
                <div key={call.id} style={{
                  display:"flex", alignItems:"center", gap:10, padding:"10px 0",
                  borderBottom: i < DEMO_CALLS.length-1 ? `1px solid ${T.border}` : "none",
                }}>
                  <div style={{
                    width:30, height:30, borderRadius:"50%", flexShrink:0,
                    display:"flex", alignItems:"center", justifyContent:"center",
                    background:c+"18", border:`1px solid ${c}30`,
                    fontSize:12, color:c,
                  }}>◎</div>
                  <div style={{ flex:1, minWidth:0 }}>
                    <p style={{ fontSize:12, fontWeight:600, color:T.dim1,
                                whiteSpace:"nowrap", overflow:"hidden", textOverflow:"ellipsis" }}>
                      {call.name}
                    </p>
                    <p style={{ fontSize:10, color:T.dim3 }}>{call.intent} · {call.dur}</p>
                  </div>
                  <span style={{
                    fontSize:10, fontWeight:600, padding:"2px 8px", borderRadius:100, flexShrink:0,
                    background:c+"18", color:c, border:`1px solid ${c}30`,
                  }}>{call.outcome}</span>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Bottom metrics */}
      <div style={{ display:"grid", gridTemplateColumns:"repeat(4,1fr)", gap:14 }}>
        {[
          { label:"AI cost today",         value:`$${(0.22*callCount).toFixed(2)}`, sub:"Ollama 80% free", color:T.teal   },
          { label:"Avg handle time",        value:"3m 07s",  sub:"per call",           color:T.blue   },
          { label:"Patient satisfaction",   value:"4.9/5",   sub:"post-call survey",   color:T.amber  },
          { label:"Calls in queue",         value:"0",       sub:"none waiting",        color:T.green  },
        ].map(s => (
          <div key={s.label} style={{ background:T.surface, border:`1px solid ${T.border}`,
                                      borderRadius:14, padding:"14px 16px" }}>
            <p style={{ fontSize:10, fontWeight:700, letterSpacing:"0.1em",
                        textTransform:"uppercase", color:T.dim3 }}>{s.label}</p>
            <p style={{ fontSize:24, fontWeight:900, letterSpacing:"-0.04em",
                        color:s.color, marginTop:6 }}>{s.value}</p>
            <p style={{ fontSize:11, color:T.dim3, marginTop:4 }}>{s.sub}</p>
          </div>
        ))}
      </div>
    </div>
  );

  // ── Patients page ──
  const PatientsPage = () => {
    const DEMO_PATIENTS = [
      { id:1, name:"Maria Santos",    dob:"1985-03-15", phone:"+1 (212) 555-1234", ins:"BlueCross" },
      { id:2, name:"James Mitchell",  dob:"1972-11-08", phone:"+1 (917) 555-5678", ins:"Aetna" },
      { id:3, name:"Priya Sharma",    dob:"1990-07-22", phone:"+1 (646) 555-9012", ins:"United" },
      { id:4, name:"Amaka Obi",       dob:"1990-03-15", phone:"+234 803 123 4567", ins:"NHIS" },
      { id:5, name:"Robert Chen",     dob:"1965-04-30", phone:"+1 (718) 555-3456", ins:"Medicare" },
    ];
    return (
      <div style={{ display:"flex", flexDirection:"column", gap:16 }}>
        <div style={{ display:"flex", alignItems:"center", justifyContent:"space-between" }}>
          <div>
            <h1 style={{ fontSize:20, fontWeight:900, color:T.white }}>Patients</h1>
            <p style={{ fontSize:13, color:T.dim3, marginTop:2 }}>{DEMO_PATIENTS.length} records</p>
          </div>
          <div style={{ display:"flex", gap:10 }}>
            <input placeholder="Search by name or phone…"
              style={{ background:T.surface, border:`1px solid ${T.border}`, borderRadius:12,
                       padding:"9px 14px", color:T.dim1, fontSize:13, outline:"none", width:240 }} />
            <button style={{
              background:T.tealDim, border:`1px solid ${T.tealBorder}`, borderRadius:12,
              padding:"9px 18px", color:T.teal, fontSize:13, fontWeight:600, cursor:"pointer",
            }}>+ Add Patient</button>
          </div>
        </div>
        <div style={{ background:T.surface, border:`1px solid ${T.border}`, borderRadius:18, overflow:"hidden" }}>
          <table style={{ width:"100%", borderCollapse:"collapse" }}>
            <thead>
              <tr style={{ borderBottom:`1px solid ${T.border}` }}>
                {["Patient","Date of Birth","Phone","Insurance","Status"].map(h => (
                  <th key={h} style={{ textAlign:"left", padding:"12px 20px", fontSize:10,
                                       fontWeight:700, letterSpacing:"0.1em",
                                       textTransform:"uppercase", color:T.dim3 }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {DEMO_PATIENTS.map((p, i) => (
                <tr key={p.id} style={{ borderBottom: i < DEMO_PATIENTS.length-1 ? `1px solid ${T.border}` : "none" }}>
                  <td style={{ padding:"12px 20px" }}>
                    <div style={{ display:"flex", alignItems:"center", gap:10 }}>
                      <div style={{
                        width:32, height:32, borderRadius:"50%", flexShrink:0,
                        display:"flex", alignItems:"center", justifyContent:"center",
                        background:T.tealDim, border:`1px solid ${T.tealBorder}`,
                        fontSize:11, fontWeight:700, color:T.teal,
                      }}>
                        {p.name.split(" ").map(n => n[0]).join("")}
                      </div>
                      <span style={{ fontSize:13, fontWeight:600, color:T.dim1 }}>{p.name}</span>
                    </div>
                  </td>
                  <td style={{ padding:"12px 20px", fontSize:13, color:T.dim2 }}>{p.dob}</td>
                  <td style={{ padding:"12px 20px", fontSize:13, fontFamily:"monospace", color:T.dim2 }}>{p.phone}</td>
                  <td style={{ padding:"12px 20px", fontSize:13, color:T.dim2 }}>{p.ins}</td>
                  <td style={{ padding:"12px 20px" }}>
                    <span style={{
                      fontSize:11, fontWeight:600, padding:"3px 10px", borderRadius:100,
                      background:T.tealDim, color:T.teal, border:`1px solid ${T.tealBorder}`,
                    }}>Active</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    );
  };

  const pageContent = {
    dashboard:    <CommandCentre />,
    patients:     <PatientsPage />,
    settings:     <SettingsPanel />,
  };

  const defaultPage = (
    <div style={{ display:"flex", alignItems:"center", justifyContent:"center",
                  height:"60vh", flexDirection:"column", gap:12 }}>
      <div style={{ width:48, height:48, borderRadius:14, background:T.tealDim,
                    border:`1px solid ${T.tealBorder}`, display:"flex", alignItems:"center",
                    justifyContent:"center", fontSize:22, color:T.teal }}>
        {NAV.find(n => n.id === page)?.icon ?? "◈"}
      </div>
      <p style={{ fontSize:15, fontWeight:600, color:T.dim2 }}>
        {NAV.find(n => n.id === page)?.label ?? page}
      </p>
      <p style={{ fontSize:12, color:T.dim3 }}>Click Command in the sidebar to see the full dashboard</p>
    </div>
  );

  return (
    <div style={{ display:"flex", minHeight:"100vh", background:T.bg, fontFamily:"-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif" }}>
      <style>{`
        @keyframes ping {
          75%, 100% { transform: scale(2); opacity: 0; }
        }
        * { box-sizing: border-box; }
        select option { background: #0F1729; }
        ::-webkit-scrollbar { width: 4px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 4px; }
      `}</style>

      <Sidebar />

      <main style={{ marginLeft:224, flex:1, padding:24, minHeight:"100vh" }}>
        {pageContent[page] ?? defaultPage}
      </main>
    </div>
  );
}
