import { useState } from "react";

const T = {
  bg:"#0B1120", surface:"#0F1729", surfaceHi:"#141E35",
  border:"rgba(255,255,255,0.07)", borderHi:"rgba(255,255,255,0.14)",
  teal:"#00E5CC", tealDim:"rgba(0,229,204,0.12)", tealBorder:"rgba(0,229,204,0.2)",
  amber:"#F5A623", amberDim:"rgba(245,166,35,0.12)",
  green:"#34D399", greenDim:"rgba(52,211,153,0.12)",
  red:"#FF4D6A", white:"#FFFFFF",
  dim1:"rgba(255,255,255,0.78)", dim2:"rgba(255,255,255,0.48)",
  dim3:"rgba(255,255,255,0.22)", dim4:"rgba(255,255,255,0.07)",
  purple:"#A78BFA",
};

const S = (extra={}) => ({
  fontFamily:"-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif",
  boxSizing:"border-box", margin:0, padding:0, ...extra
});

const STEPS = [
  {num:1,icon:"◉",title:"Clinic Details",      desc:"Tell us about your practice"},
  {num:2,icon:"◈",title:"EHR Connection",       desc:"Connect your system or go standalone"},
  {num:3,icon:"◎",title:"Voice & Messaging",    desc:"How patients reach you"},
  {num:4,icon:"◈",title:"Agent Setup",          desc:"Choose what AI handles"},
  {num:5,icon:"◫",title:"HIPAA Agreement",      desc:"Required for US patient data"},
  {num:6,icon:"▦",title:"Test Call",            desc:"Verify everything works"},
  {num:7,icon:"⚡",title:"Go Live",             desc:"Your AI receptionist is ready"},
];

const EHR_OPTS = [
  {v:"standalone",    l:"Standalone — No EHR",    b:"Global",     hi:true},
  {v:"athenahealth",  l:"athenahealth",            b:"US",         hi:false},
  {v:"modmed",        l:"ModMed EMA",              b:"Specialty",  hi:false},
  {v:"epic",          l:"Epic (SMART on FHIR)",    b:"Enterprise", hi:false},
  {v:"eclinicalworks",l:"eClinicalWorks",          b:"US",         hi:false},
  {v:"helium_health", l:"Helium Health",           b:"Nigeria",    hi:false},
  {v:"cerner",        l:"Cerner / Oracle Health",  b:"Enterprise", hi:false},
  {v:"openmrs",       l:"OpenMRS",                 b:"Africa",     hi:false},
];

const AGENTS = [
  {id:"reception",  l:"Reception",  d:"Answers every call in 600ms",     req:true},
  {id:"scheduling", l:"Scheduling", d:"Books into EHR automatically",    req:true},
  {id:"intake",     l:"Intake",     d:"Collects patient info pre-visit", req:false},
  {id:"insurance",  l:"Insurance",  d:"Real-time eligibility checks",    req:false},
  {id:"prior_auth", l:"Prior Auth", d:"Automated PA submissions",        req:false},
  {id:"refill",     l:"Refills",    d:"Prescription handling",           req:false},
  {id:"records",    l:"Records",    d:"HIPAA-compliant release",         req:false},
  {id:"referrals",  l:"Referrals",  d:"Specialist tracking",             req:false},
  {id:"recall",     l:"Recalls",    d:"Proactive outreach",              req:false},
  {id:"email",      l:"Email",      d:"Inbox triage",                    req:false},
];

function Btn({children, onClick, disabled, primary=true, small=false}) {
  return (
    <button onClick={onClick} disabled={disabled} style={S({
      padding: small ? "8px 16px" : "13px 20px",
      borderRadius:11, fontSize: small ? 12 : 14, fontWeight:700,
      width: small ? "auto" : "100%",
      cursor: disabled ? "not-allowed" : "pointer",
      border:"none", transition:"all 0.15s",
      background: disabled ? T.dim4 : primary
        ? "linear-gradient(135deg,#00E5CC,#0099BB)" : T.tealDim,
      color: disabled ? T.dim3 : primary ? "#070C17" : T.teal,
    })}>{children}</button>
  );
}

function Field({label, value, onChange, placeholder, type="text"}) {
  return (
    <div>
      <p style={S({fontSize:10,fontWeight:700,letterSpacing:"0.1em",
        textTransform:"uppercase",color:T.dim3,marginBottom:6})}>{label}</p>
      <input type={type} value={value} onChange={e=>onChange(e.target.value)}
        placeholder={placeholder}
        style={S({width:"100%",padding:"11px 14px",borderRadius:10,
          background:T.dim4,border:`1px solid ${T.border}`,
          color:T.dim1,fontSize:13,outline:"none"})}/>
    </div>
  );
}

// ── Step pages ────────────────────────────────────────────────────────────────

function StepClinic({onNext}) {
  const [name,setName]=useState("");
  const [country,setCountry]=useState("US");
  const [specialty,setSpecialty]=useState("Family Medicine");
  const [providers,setProviders]=useState("3-5");

  return (
    <div style={S({display:"flex",flexDirection:"column",gap:14})}>
      <Field label="Clinic / Hospital Name *" value={name} onChange={setName}
        placeholder="e.g. Family Care Associates" />
      <div style={S({display:"grid",gridTemplateColumns:"1fr 1fr",gap:12})}>
        <div>
          <p style={S({fontSize:10,fontWeight:700,letterSpacing:"0.1em",
            textTransform:"uppercase",color:T.dim3,marginBottom:6})}>Country</p>
          <select value={country} onChange={e=>setCountry(e.target.value)}
            style={S({width:"100%",padding:"11px 14px",borderRadius:10,
              background:T.surface,border:`1px solid ${T.border}`,
              color:T.dim1,fontSize:13,outline:"none",cursor:"pointer"})}>
            <option value="US">🇺🇸 United States</option>
            <option value="NG">🇳🇬 Nigeria</option>
            <option value="KE">🇰🇪 Kenya</option>
            <option value="GH">🇬🇭 Ghana</option>
            <option value="GB">🇬🇧 United Kingdom</option>
            <option value="PH">🇵🇭 Philippines</option>
          </select>
        </div>
        <div>
          <p style={S({fontSize:10,fontWeight:700,letterSpacing:"0.1em",
            textTransform:"uppercase",color:T.dim3,marginBottom:6})}>Specialty</p>
          <select value={specialty} onChange={e=>setSpecialty(e.target.value)}
            style={S({width:"100%",padding:"11px 14px",borderRadius:10,
              background:T.surface,border:`1px solid ${T.border}`,
              color:T.dim1,fontSize:13,outline:"none",cursor:"pointer"})}>
            {["Family Medicine","Internal Medicine","Pediatrics","Dermatology",
              "Mental Health","Dental","General Practice"].map(s=>(
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
        </div>
      </div>
      <div>
        <p style={S({fontSize:10,fontWeight:700,letterSpacing:"0.1em",
          textTransform:"uppercase",color:T.dim3,marginBottom:6})}>Number of Providers</p>
        <select value={providers} onChange={e=>setProviders(e.target.value)}
          style={S({width:"100%",padding:"11px 14px",borderRadius:10,
            background:T.surface,border:`1px solid ${T.border}`,
            color:T.dim1,fontSize:13,outline:"none",cursor:"pointer"})}>
          <option value="1-2">1–2 providers — Starter ($499/mo · ₦25,000/mo)</option>
          <option value="3-5">3–5 providers — Pro ($999/mo · ₦49,000/mo)</option>
          <option value="6-15">6–15 providers — Growth ($1,999/mo)</option>
          <option value="15+">15+ providers — Enterprise ($3,999/mo)</option>
        </select>
      </div>
      <Btn onClick={()=>onNext({name,country,specialty,providers})} disabled={!name}>
        Continue →
      </Btn>
    </div>
  );
}

function StepEHR({country, onNext}) {
  const [ehr,setEhr]=useState("standalone");
  const [cid,setCid]=useState("");
  const [cs,setCs]=useState("");
  const [connStatus,setConnStatus]=useState("idle");
  const isStandalone = ehr==="standalone";

  const test = async () => {
    setConnStatus("testing");
    await new Promise(r=>setTimeout(r,1600));
    setConnStatus(cid?"ok":"fail");
  };

  return (
    <div style={S({display:"flex",flexDirection:"column",gap:14})}>
      <div style={S({display:"grid",gridTemplateColumns:"1fr 1fr",gap:8})}>
        {EHR_OPTS.map(o=>(
          <button key={o.v} onClick={()=>{setEhr(o.v);setConnStatus("idle");}}
            style={S({
              padding:"11px 12px",borderRadius:10,textAlign:"left",
              background:ehr===o.v?(o.hi?T.tealDim:T.surfaceHi):T.dim4,
              border:`1px solid ${ehr===o.v?(o.hi?T.tealBorder:T.borderHi):T.border}`,
              cursor:"pointer",transition:"all 0.12s",
            })}>
            <div style={S({display:"flex",alignItems:"center",justifyContent:"space-between"})}>
              <span style={S({fontSize:12,fontWeight:600,
                color:ehr===o.v?T.dim1:T.dim2})}>{o.l}</span>
              <span style={S({fontSize:9,fontWeight:700,padding:"2px 6px",borderRadius:100,
                background:o.hi?T.tealDim:T.dim4,
                color:o.hi?T.teal:T.dim3})}>{o.b}</span>
            </div>
          </button>
        ))}
      </div>

      {isStandalone ? (
        <div style={S({background:T.tealDim,border:`1px solid ${T.tealBorder}`,
          borderRadius:11,padding:"14px 16px",display:"flex",gap:10})}>
          <span style={{color:T.teal,fontSize:18,flexShrink:0}}>◈</span>
          <div>
            <p style={S({fontSize:13,fontWeight:700,color:T.teal,marginBottom:4})}>
              Standalone Mode
            </p>
            <p style={S({fontSize:12,color:T.dim2,lineHeight:1.5})}>
              No EHR needed. Carenova stores all patient records directly.
              Perfect for paper-based hospitals and new clinics.
              Connect an EHR anytime — your data is always preserved.
            </p>
          </div>
        </div>
      ):(
        <div style={S({display:"grid",gridTemplateColumns:"1fr 1fr",gap:12})}>
          <Field label="Client ID" value={cid} onChange={setCid} placeholder="Client ID"/>
          <Field label="Client Secret" value={cs} onChange={setCs} placeholder="••••••" type="password"/>
          <div style={S({display:"flex",alignItems:"flex-end",gap:10})}>
            <button onClick={test} style={S({
              flex:1,padding:"11px",borderRadius:10,fontSize:13,fontWeight:600,
              background:T.tealDim,border:`1px solid ${T.tealBorder}`,
              color:T.teal,cursor:"pointer",
            })}>
              {connStatus==="testing"?"Testing…":"Test Connection"}
            </button>
            {connStatus==="ok" && <span style={{color:T.green,fontSize:14}}>✓</span>}
            {connStatus==="fail" && <span style={{color:T.red,fontSize:14}}>✗</span>}
          </div>
        </div>
      )}

      <Btn onClick={()=>onNext({ehr_type:ehr})}
        disabled={!isStandalone && connStatus!=="ok"}>
        {isStandalone?"Continue with Standalone →":"Continue →"}
      </Btn>
    </div>
  );
}

function StepVoice({country, onNext}) {
  const [retell,setRetell]=useState("");
  const [wa,setWa]=useState("");
  const [greeting,setGreeting]=useState("Thank you for calling. How can I help you today?");
  const isNG = country==="NG";

  return (
    <div style={S({display:"flex",flexDirection:"column",gap:14})}>
      {!isNG&&(
        <div>
          <Field label="Retell AI API Key (US voice calls)" value={retell}
            onChange={setRetell} placeholder="Get free at app.retellai.com" type="password"/>
          <p style={S({fontSize:11,color:T.dim3,marginTop:5})}>
            HIPAA BAA signed · $0.07/min · 600ms answer time
          </p>
        </div>
      )}
      <div>
        <Field label={`WhatsApp Number ${isNG?"(Required)":"(Optional)"}`} value={wa}
          onChange={setWa} placeholder="+234 803 000 0000"/>
        <p style={S({fontSize:11,color:T.dim3,marginTop:5})}>
          Patients book via WhatsApp · Works on 2G
        </p>
      </div>
      <Field label="AI Greeting" value={greeting} onChange={setGreeting}
        placeholder="Thank you for calling…"/>
      <Btn onClick={()=>onNext({retell,whatsapp:wa,greeting})}
        disabled={!retell&&!wa}>
        Continue →
      </Btn>
    </div>
  );
}

function StepAgents({onNext}) {
  const [enabled,setEnabled]=useState(
    AGENTS.filter(a=>a.req||["intake","refill","recall"].includes(a.id)).map(a=>a.id)
  );
  const toggle=(id,req)=>{
    if(req)return;
    setEnabled(p=>p.includes(id)?p.filter(x=>x!==id):[...p,id]);
  };
  return (
    <div style={S({display:"flex",flexDirection:"column",gap:12})}>
      <div style={S({display:"grid",gridTemplateColumns:"1fr 1fr",gap:8})}>
        {AGENTS.map(a=>{
          const on=enabled.includes(a.id);
          return(
            <button key={a.id} onClick={()=>toggle(a.id,a.req)}
              style={S({
                padding:"11px 12px",borderRadius:11,textAlign:"left",
                background:on?T.surfaceHi:T.dim4,
                border:`1px solid ${on?T.tealBorder:T.border}`,
                cursor:a.req?"default":"pointer",transition:"all 0.12s",
              })}>
              <div style={S({display:"flex",alignItems:"center",gap:7,marginBottom:3})}>
                <div style={S({width:6,height:6,borderRadius:"50%",flexShrink:0,
                  background:on?T.teal:T.dim3,
                  boxShadow:on?`0 0 6px ${T.teal}`:undefined})}/>
                <span style={S({fontSize:12,fontWeight:600,
                  color:on?T.dim1:T.dim3})}>{a.l}</span>
                {a.req&&<span style={S({fontSize:9,color:T.teal,marginLeft:"auto"})}>ON</span>}
              </div>
              <p style={S({fontSize:10,color:on?T.dim3:"rgba(255,255,255,0.12)",
                margin:"0 0 0 13px",lineHeight:1.4})}>{a.d}</p>
            </button>
          );
        })}
      </div>
      <p style={S({fontSize:11,color:T.dim3,textAlign:"center"})}>
        {enabled.length} agents enabled
      </p>
      <Btn onClick={()=>onNext({enabled_agents:enabled})} disabled={false}>
        Continue with {enabled.length} agents →
      </Btn>
    </div>
  );
}

function StepBAA({country, clinicName, onNext}) {
  const [sigName,setSigName]=useState("");
  const [sigTitle,setSigTitle]=useState("");
  const [agreed,setAgreed]=useState(false);
  const isNG = country==="NG";

  if(isNG) return (
    <div style={S({display:"flex",flexDirection:"column",gap:14})}>
      <div style={S({background:T.greenDim,border:`1px solid ${T.green}30`,
        borderRadius:11,padding:"16px 18px",display:"flex",gap:12})}>
        <span style={{color:T.green,fontSize:20,flexShrink:0}}>✓</span>
        <div>
          <p style={S({fontSize:13,fontWeight:700,color:T.green,marginBottom:4})}>
            NDPR Compliant — Nigeria
          </p>
          <p style={S({fontSize:12,color:T.dim2,lineHeight:1.5})}>
            Your clinic operates under Nigeria Data Protection Regulation (NDPR).
            No US HIPAA BAA required. Carenova is fully NDPR compliant.
          </p>
        </div>
      </div>
      <Btn onClick={()=>onNext({skipped:true})}>Continue →</Btn>
    </div>
  );

  return (
    <div style={S({display:"flex",flexDirection:"column",gap:14})}>
      <div style={S({background:T.dim4,border:`1px solid ${T.border}`,
        borderRadius:10,padding:"14px 16px",maxHeight:140,overflowY:"auto"})}>
        <p style={S({fontSize:11,color:T.dim3,lineHeight:1.7})}>
          <strong style={{color:T.dim1}}>BUSINESS ASSOCIATE AGREEMENT</strong>
          <br/><br/>
          This BAA is between <strong style={{color:T.dim1}}>{clinicName||"your clinic"}</strong> and
          Tinlance Limited (RC: 7962164). Tinlance agrees to implement all HIPAA-required
          administrative, physical, and technical safeguards; encrypt all PHI in transit (TLS 1.3)
          and at rest (AES-256); maintain audit logs per §164.312(b); notify you of any breach
          within 60 days; and sign BAAs with all sub-processors including Retell AI, Supabase, and AWS.
          This agreement complies with 45 CFR Part 164 and becomes effective upon electronic execution.
        </p>
      </div>
      <div style={S({display:"grid",gridTemplateColumns:"1fr 1fr",gap:12})}>
        <Field label="Your Full Name *" value={sigName} onChange={setSigName}
          placeholder="Dr. James Chen"/>
        <Field label="Your Title *" value={sigTitle} onChange={setSigTitle}
          placeholder="Medical Director"/>
      </div>
      <button onClick={()=>setAgreed(!agreed)}
        style={S({display:"flex",alignItems:"center",gap:10,
          background:"none",border:"none",cursor:"pointer",padding:0})}>
        <div style={S({width:18,height:18,borderRadius:5,flexShrink:0,
          background:agreed?T.teal:"transparent",
          border:`2px solid ${agreed?T.teal:T.dim3}`,
          display:"flex",alignItems:"center",justifyContent:"center"})}>
          {agreed&&<span style={{color:"#070C17",fontSize:11,fontWeight:900}}>✓</span>}
        </div>
        <span style={S({fontSize:12,color:T.dim2,textAlign:"left"})}>
          I agree to the BAA on behalf of {clinicName||"my clinic"}. This is a legally binding electronic signature.
        </span>
      </button>
      <Btn onClick={()=>onNext({signatory_name:sigName,signatory_title:sigTitle})}
        disabled={!sigName||!sigTitle||!agreed}>
        Sign BAA & Continue →
      </Btn>
    </div>
  );
}

function StepTest({onNext}) {
  const [phone,setPhone]=useState("");
  const [status,setStatus]=useState("idle");

  const call = async ()=>{
    setStatus("calling");
    await new Promise(r=>setTimeout(r,2500));
    setStatus("success");
  };

  return (
    <div style={S({display:"flex",flexDirection:"column",gap:14})}>
      <div style={S({background:T.surface,border:`1px solid ${T.border}`,
        borderRadius:11,padding:"16px 18px"})}>
        {[
          "Carenova answers in under 1 second",
          "AI greets you with your custom message",
          "Ask to book an appointment — AI responds",
          "Check your dashboard — call logged live",
        ].map((t,i)=>(
          <div key={i} style={S({display:"flex",gap:10,
            marginBottom:i<3?10:0})}>
            <div style={S({width:20,height:20,borderRadius:"50%",flexShrink:0,
              background:T.tealDim,border:`1px solid ${T.tealBorder}`,
              display:"flex",alignItems:"center",justifyContent:"center",
              fontSize:10,fontWeight:700,color:T.teal})}>{i+1}</div>
            <p style={S({fontSize:13,color:T.dim2,paddingTop:3})}>{t}</p>
          </div>
        ))}
      </div>

      {status==="idle"&&(
        <>
          <Field label="Your phone number" value={phone} onChange={setPhone}
            placeholder="+1 (555) 000-0000"/>
          <Btn onClick={call} disabled={!phone}>📞 Start Test Call</Btn>
          <button onClick={()=>onNext({skipped:true})}
            style={S({background:"none",border:"none",color:T.dim3,
              fontSize:12,cursor:"pointer",textDecoration:"underline"})}>
            Skip — I'll test later
          </button>
        </>
      )}

      {status==="calling"&&(
        <div style={S({textAlign:"center",padding:"20px 0"})}>
          <p style={S({fontSize:36,marginBottom:10})}>📞</p>
          <p style={S({fontSize:13,fontWeight:700,color:T.teal,marginBottom:6})}>
            Calling {phone}…
          </p>
          <p style={S({fontSize:11,color:T.dim3})}>
            Pick up and say "I want to book an appointment"
          </p>
        </div>
      )}

      {status==="success"&&(
        <div style={S({display:"flex",flexDirection:"column",gap:12})}>
          <div style={S({background:T.greenDim,border:`1px solid ${T.green}30`,
            borderRadius:11,padding:"14px 16px",display:"flex",gap:10})}>
            <span style={{color:T.green,fontSize:18}}>✓</span>
            <div>
              <p style={S({fontSize:13,fontWeight:700,color:T.green,marginBottom:3})}>Test passed!</p>
              <p style={S({fontSize:12,color:T.dim2})}>AI answered and responded correctly. Ready to go live.</p>
            </div>
          </div>
          <Btn onClick={()=>onNext({test_passed:true})}>Go Live →</Btn>
        </div>
      )}
    </div>
  );
}

function StepLive({clinicName, country, setScreen}) {
  const prices = {US:"$999/month",NG:"₦49,000/month",KE:"KES 12,900/month",GB:"£799/month"};
  return (
    <div style={S({display:"flex",flexDirection:"column",gap:18,textAlign:"center"})}>
      <div>
        <p style={S({fontSize:48,marginBottom:14})}>🎉</p>
        <h2 style={S({fontSize:22,fontWeight:900,color:T.white,
          letterSpacing:"-0.02em",marginBottom:10})}>
          {clinicName||"Your clinic"} is live!
        </h2>
        <p style={S({fontSize:13,color:T.dim2,lineHeight:1.7})}>
          Your AI receptionist is now answering calls in 600ms.
          Every call logged. Every appointment booked.
          Your staff never misses a patient again.
        </p>
      </div>
      <div style={S({display:"grid",gridTemplateColumns:"1fr 1fr 1fr",gap:10})}>
        {[
          {icon:"◎",l:"Call answering",d:"600ms. 24/7.",c:T.teal},
          {icon:"◉",l:"Patient records",d:"Stored securely",c:T.green},
          {icon:"▦",l:"EHR write-back",d:"Automatic",c:T.purple},
        ].map(f=>(
          <div key={f.l} style={S({background:T.surface,border:`1px solid ${T.border}`,
            borderRadius:11,padding:"14px 10px"})}>
            <p style={S({fontSize:18,color:f.c,marginBottom:6})}>{f.icon}</p>
            <p style={S({fontSize:12,fontWeight:700,color:T.dim1,marginBottom:3})}>{f.l}</p>
            <p style={S({fontSize:11,color:T.dim3})}>{f.d}</p>
          </div>
        ))}
      </div>
      <div style={S({background:T.tealDim,border:`1px solid ${T.tealBorder}`,
        borderRadius:11,padding:"12px 16px"})}>
        <p style={S({fontSize:12,color:T.dim2,marginBottom:4})}>
          30-day free trial active. No payment needed yet.
        </p>
        <p style={S({fontSize:11,color:T.dim3})}>
          After that: {prices[country]||"$999/month"} · Cancel anytime
        </p>
      </div>
      <Btn onClick={()=>setScreen("dashboard")}>Open Dashboard →</Btn>
    </div>
  );
}

// ── Main app ──────────────────────────────────────────────────────────────────

export default function OnboardingPreview() {
  const [screen, setScreen] = useState("landing");
  const [step, setStep] = useState(1);
  const [data, setData] = useState({country:"US", name:""});

  const next = (stepData) => {
    setData(d=>({...d,...stepData}));
    if(step<7) setStep(s=>s+1);
  };

  // Landing page preview
  if(screen==="landing") return (
    <div style={S({minHeight:"100vh",background:T.bg,display:"flex",
      flexDirection:"column",alignItems:"center",justifyContent:"center",
      padding:40,gap:20})}>
      <div style={S({width:52,height:52,borderRadius:14,
        background:"linear-gradient(135deg,#00E5CC,#0099BB)",
        display:"flex",alignItems:"center",justifyContent:"center",
        fontSize:22,fontWeight:900,color:"#070C17"})}>C</div>
      <div style={S({textAlign:"center",maxWidth:520})}>
        <h1 style={S({fontSize:36,fontWeight:900,color:T.white,
          letterSpacing:"-0.04em",lineHeight:1.1,marginBottom:14})}>
          Never miss another<br/>
          <span style={{color:T.teal}}>patient call.</span>
        </h1>
        <p style={S({fontSize:15,color:T.dim2,lineHeight:1.7,marginBottom:28})}>
          AI answers every call in 600ms, books directly into your EHR,
          and costs $999/month. Your $3,100 receptionist is optional.
        </p>
        <div style={S({display:"flex",gap:10,justifyContent:"center",flexWrap:"wrap"})}>
          <button onClick={()=>setScreen("signup")}
            style={S({background:"linear-gradient(135deg,#00E5CC,#0099BB)",
              border:"none",borderRadius:11,padding:"13px 28px",
              color:"#070C17",fontSize:14,fontWeight:700,cursor:"pointer"})}>
            Start free 30-day trial →
          </button>
          <button onClick={()=>setScreen("onboarding")}
            style={S({background:T.tealDim,border:`1px solid ${T.tealBorder}`,
              borderRadius:11,padding:"13px 28px",
              color:T.teal,fontSize:14,fontWeight:700,cursor:"pointer"})}>
            See onboarding flow →
          </button>
        </div>
        <p style={S({fontSize:11,color:T.dim3,marginTop:16})}>
          HIPAA ✓ · NDPR ✓ · Works globally · No credit card required
        </p>
      </div>
    </div>
  );

  // Sign up preview
  if(screen==="signup") return (
    <div style={S({minHeight:"100vh",background:T.bg,display:"flex",
      flexDirection:"column",alignItems:"center",justifyContent:"center",padding:40})}>
      <div style={S({width:"100%",maxWidth:400})}>
        <div style={S({textAlign:"center",marginBottom:28})}>
          <div style={S({display:"inline-flex",alignItems:"center",justifyContent:"center",
            width:44,height:44,borderRadius:12,
            background:"linear-gradient(135deg,#00E5CC,#0099BB)",
            marginBottom:16,fontSize:20,fontWeight:900,color:"#070C17"})}>C</div>
          <h1 style={S({fontSize:20,fontWeight:800,color:T.white,margin:"0 0 6px"})}>
            Start your free trial
          </h1>
          <p style={S({fontSize:12,color:T.dim3,margin:0})}>
            30 days free · No credit card required
          </p>
        </div>
        <div style={S({background:T.surface,border:`1px solid ${T.border}`,
          borderRadius:16,padding:24,display:"flex",flexDirection:"column",gap:12})}>
          <Field label="Full Name" value="" onChange={()=>{}} placeholder="Dr. James Chen"/>
          <Field label="Work Email" value="" onChange={()=>{}} placeholder="doctor@yourclinic.com"/>
          <Field label="Password" value="" onChange={()=>{}} placeholder="••••••••" type="password"/>
          <button onClick={()=>setScreen("onboarding")}
            style={S({background:"linear-gradient(135deg,#00E5CC,#0099BB)",
              border:"none",borderRadius:11,padding:"13px",
              color:"#070C17",fontSize:14,fontWeight:700,cursor:"pointer",
              marginTop:4})}>
            Create account →
          </button>
          <p style={S({fontSize:11,color:T.dim3,textAlign:"center"})}>
            Already have an account?{" "}
            <span style={{color:T.teal,cursor:"pointer"}}>Sign in →</span>
          </p>
        </div>
      </div>
    </div>
  );

  // Dashboard preview
  if(screen==="dashboard") return (
    <div style={S({minHeight:"100vh",background:T.bg,display:"flex",
      flexDirection:"column",alignItems:"center",justifyContent:"center",padding:40,gap:20})}>
      <div style={S({textAlign:"center"})}>
        <p style={S({fontSize:48,marginBottom:16})}>✅</p>
        <h2 style={S({fontSize:22,fontWeight:900,color:T.white,marginBottom:10})}>
          Welcome to your dashboard
        </h2>
        <p style={S({fontSize:13,color:T.dim2,marginBottom:24})}>
          {data.name||"Your clinic"} is live. First call can come in now.
        </p>
        <button onClick={()=>{setScreen("landing");setStep(1);setData({country:"US",name:""}); }}
          style={S({background:T.tealDim,border:`1px solid ${T.tealBorder}`,
            borderRadius:11,padding:"11px 24px",color:T.teal,
            fontSize:13,fontWeight:600,cursor:"pointer"})}>
          ← Start over
        </button>
      </div>
    </div>
  );

  // Onboarding wizard
  const currentStep = STEPS.find(s=>s.num===step)||STEPS[0];

  return (
    <div style={S({minHeight:"100vh",background:T.bg,display:"flex",
      alignItems:"flex-start",justifyContent:"center",padding:"32px 20px"})}>
      <div style={S({width:"100%",maxWidth:560})}>

        {/* Logo */}
        <div style={S({display:"flex",alignItems:"center",gap:9,marginBottom:28})}>
          <div style={S({width:30,height:30,borderRadius:8,
            background:"linear-gradient(135deg,#00E5CC,#0099BB)",
            display:"flex",alignItems:"center",justifyContent:"center",
            fontWeight:900,fontSize:13,color:"#070C17"})}>C</div>
          <span style={S({fontSize:13,fontWeight:700,color:T.white})}>Carenova</span>
          <span style={S({marginLeft:"auto",fontSize:11,color:T.dim3})}>
            Step {step} of 7 · ~{(7-step)*2}min left
          </span>
        </div>

        {/* Progress */}
        <div style={S({marginBottom:24})}>
          <div style={S({height:3,borderRadius:3,background:T.dim4,overflow:"hidden",marginBottom:8})}>
            <div style={S({height:"100%",borderRadius:3,
              width:`${(step/7)*100}%`,
              background:"linear-gradient(90deg,#00E5CC,#0099BB)",
              transition:"width 0.4s ease"})}/>
          </div>
          <div style={S({display:"flex",gap:3})}>
            {STEPS.map(s=>(
              <div key={s.num} style={S({flex:1,height:2,borderRadius:2,
                background:s.num<step?T.teal:s.num===step?T.tealBorder:T.dim4,
                transition:"background 0.3s"})}/>
            ))}
          </div>
        </div>

        {/* Step header */}
        <div style={S({display:"flex",alignItems:"center",gap:12,marginBottom:22})}>
          <div style={S({width:38,height:38,borderRadius:10,
            background:T.tealDim,border:`1px solid ${T.tealBorder}`,
            display:"flex",alignItems:"center",justifyContent:"center",
            fontSize:17,color:T.teal})}>{currentStep.icon}</div>
          <div>
            <p style={S({fontSize:17,fontWeight:800,color:T.white,margin:0,
              letterSpacing:"-0.02em"})}>{currentStep.title}</p>
            <p style={S({fontSize:11,color:T.dim3,margin:0})}>{currentStep.desc}</p>
          </div>
        </div>

        {/* Content */}
        <div style={S({background:T.surface,border:`1px solid ${T.border}`,
          borderRadius:16,padding:22})}>
          {step===1&&<StepClinic onNext={next}/>}
          {step===2&&<StepEHR country={data.country} onNext={next}/>}
          {step===3&&<StepVoice country={data.country} onNext={next}/>}
          {step===4&&<StepAgents onNext={next}/>}
          {step===5&&<StepBAA country={data.country} clinicName={data.name} onNext={next}/>}
          {step===6&&<StepTest onNext={next}/>}
          {step===7&&<StepLive clinicName={data.name} country={data.country} setScreen={setScreen}/>}
        </div>

        {/* Step dots */}
        <div style={S({display:"flex",gap:5,justifyContent:"center",marginTop:18})}>
          {STEPS.map(s=>(
            <div key={s.num} style={S({
              width:s.num===step?22:7,height:7,borderRadius:4,
              background:s.num<step?T.teal:s.num===step?T.teal:T.dim4,
              opacity:s.num===step?1:s.num<step?0.55:0.25,
              transition:"all 0.3s",cursor:s.num<step?"pointer":"default",
            })} onClick={()=>s.num<step&&setStep(s.num)}/>
          ))}
        </div>

        {step<7&&(
          <p style={S({textAlign:"center",fontSize:11,color:T.dim3,marginTop:14})}>
            Need help?{" "}
            <span style={{color:T.teal,cursor:"pointer"}}>
              WhatsApp lloyd@tinlance.com →
            </span>
          </p>
        )}
      </div>
    </div>
  );
}
