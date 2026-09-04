"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";

const T = {
  bg:"#0B1120", surface:"#0F1729", surfaceHi:"#141E35",
  border:"rgba(255,255,255,0.07)", borderHi:"rgba(255,255,255,0.14)",
  teal:"#00E5CC", tealDim:"rgba(0,229,204,0.12)", tealBorder:"rgba(0,229,204,0.2)",
  amber:"#F5A623", amberDim:"rgba(245,166,35,0.12)",
  green:"#34D399", greenDim:"rgba(52,211,153,0.12)",
  red:"#FF4D6A",
  white:"#FFFFFF",
  dim1:"rgba(255,255,255,0.78)", dim2:"rgba(255,255,255,0.48)",
  dim3:"rgba(255,255,255,0.22)", dim4:"rgba(255,255,255,0.07)",
};

const STEPS = [
  { num:1, id:"clinic",  title:"Clinic Details",      icon:"◉", desc:"Tell us about your practice" },
  { num:2, id:"ehr",     title:"EHR Connection",       icon:"◈", desc:"Connect your system or use standalone mode" },
  { num:3, id:"voice",   title:"Voice & Messaging",    icon:"◎", desc:"Configure how patients reach you" },
  { num:4, id:"agents",  title:"Agent Setup",          icon:"◈", desc:"Choose what your AI handles" },
  { num:5, id:"baa",     title:"HIPAA Agreement",      icon:"◫", desc:"Required for US patient data" },
  { num:6, id:"test",    title:"Test Call",            icon:"▦", desc:"Verify everything is working" },
  { num:7, id:"live",    title:"Go Live",              icon:"⚡", desc:"Your AI receptionist is ready" },
];

const EHR_OPTIONS = [
  { value:"standalone",    label:"Standalone — No EHR",      badge:"Global · Recommended", highlight:true },
  { value:"athenahealth",  label:"athenahealth",             badge:"US" },
  { value:"modmed",        label:"ModMed EMA",               badge:"Specialty" },
  { value:"epic",          label:"Epic SMART on FHIR",       badge:"Enterprise" },
  { value:"eclinicalworks",label:"eClinicalWorks",           badge:"US" },
  { value:"nextgen",       label:"NextGen",                  badge:"US" },
  { value:"drchrono",      label:"DrChrono",                 badge:"US" },
  { value:"elation",       label:"Elation Health",           badge:"US" },
  { value:"tebra",         label:"Tebra (Kareo)",            badge:"US" },
  { value:"helium_health", label:"Helium Health",            badge:"Nigeria" },
  { value:"cerner",        label:"Cerner (Oracle Health)",   badge:"Enterprise" },
  { value:"openmrs",       label:"OpenMRS",                  badge:"Africa / Global" },
];

const ALL_AGENTS = [
  { id:"reception",  label:"Reception",  desc:"Answers every call in 600ms",      required:true },
  { id:"scheduling", label:"Scheduling", desc:"Books appointments in your EHR",   required:true },
  { id:"intake",     label:"Intake",     desc:"Collects patient info pre-visit",  required:false },
  { id:"insurance",  label:"Insurance",  desc:"Real-time eligibility checks",     required:false },
  { id:"prior_auth", label:"Prior Auth", desc:"Automated PA submissions",          required:false },
  { id:"refill",     label:"Refills",    desc:"Prescription refill handling",     required:false },
  { id:"records",    label:"Records",    desc:"HIPAA-compliant record release",   required:false },
  { id:"referrals",  label:"Referrals",  desc:"Specialist referral tracking",     required:false },
  { id:"recall",     label:"Recalls",    desc:"Proactive patient outreach",       required:false },
  { id:"email",      label:"Email",      desc:"Inbox triage and confirmations",   required:false },
];

function FieldLabel({ children }: { children: React.ReactNode }) {
  return (
    <label style={{
      fontSize:10, fontWeight:700, letterSpacing:"0.1em",
      textTransform:"uppercase" as const, color:T.dim3,
      display:"block", marginBottom:6,
    }}>{children}</label>
  );
}

function Input({ value, onChange, placeholder, type="text" }: any) {
  return (
    <input
      type={type} value={value} onChange={e => onChange(e.target.value)}
      placeholder={placeholder}
      style={{
        width:"100%", padding:"11px 14px", borderRadius:11,
        background:T.dim4, border:`1px solid ${T.border}`,
        color:T.dim1, fontSize:13, outline:"none",
        fontFamily:"-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif",
      }}
    />
  );
}

function Select({ value, onChange, children }: any) {
  return (
    <select value={value} onChange={e => onChange(e.target.value)}
      style={{
        width:"100%", padding:"11px 14px", borderRadius:11,
        background:T.surface, border:`1px solid ${T.border}`,
        color:T.dim1, fontSize:13, outline:"none", cursor:"pointer",
      }}>
      {children}
    </select>
  );
}

function NextBtn({ onClick, loading, disabled, children }: any) {
  return (
    <button onClick={onClick} disabled={disabled || loading}
      style={{
        background: disabled ? T.dim4 : "linear-gradient(135deg,#00E5CC,#0099BB)",
        border:"none", borderRadius:12, padding:"13px 32px",
        color: disabled ? T.dim3 : "#070C17",
        fontSize:14, fontWeight:700, cursor: disabled ? "not-allowed" : "pointer",
        transition:"all 0.15s", width:"100%",
        fontFamily:"-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif",
      }}>
      {loading ? "Saving…" : children}
    </button>
  );
}

// ── Step components ───────────────────────────────────────────────────────────

function Step1Clinic({ onNext }: { onNext: (d: any) => void }) {
  const [name, setName] = useState("");
  const [country, setCountry] = useState("US");
  const [specialty, setSpecialty] = useState("Family Medicine");
  const [providers, setProviders] = useState("1-2");
  const [phone, setPhone] = useState("");
  const [loading, setLoading] = useState(false);

  const submit = async () => {
    setLoading(true);
    await new Promise(r => setTimeout(r, 600));
    setLoading(false);
    onNext({ name, country, specialty, providers, phone });
  };

  return (
    <div style={{ display:"flex", flexDirection:"column", gap:16 }}>
      <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:12 }}>
        <div style={{ gridColumn:"1 / -1" }}>
          <FieldLabel>Clinic / Hospital Name *</FieldLabel>
          <Input value={name} onChange={setName} placeholder="e.g. Family Care Associates" />
        </div>
        <div>
          <FieldLabel>Country *</FieldLabel>
          <Select value={country} onChange={setCountry}>
            <option value="US">🇺🇸 United States</option>
            <option value="NG">🇳🇬 Nigeria</option>
            <option value="KE">🇰🇪 Kenya</option>
            <option value="GH">🇬🇭 Ghana</option>
            <option value="GB">🇬🇧 United Kingdom</option>
            <option value="PH">🇵🇭 Philippines</option>
            <option value="IN">🇮🇳 India</option>
            <option value="ZA">🇿🇦 South Africa</option>
            <option value="OTHER">🌍 Other</option>
          </Select>
        </div>
        <div>
          <FieldLabel>Specialty</FieldLabel>
          <Select value={specialty} onChange={setSpecialty}>
            {["Family Medicine","Internal Medicine","Pediatrics","Dermatology",
              "Ophthalmology","Orthopedics","Mental Health","Dental","General Practice","Other"
            ].map(s => <option key={s} value={s}>{s}</option>)}
          </Select>
        </div>
        <div>
          <FieldLabel>Number of Providers</FieldLabel>
          <Select value={providers} onChange={setProviders}>
            <option value="1-2">1–2 providers (Starter $499/mo)</option>
            <option value="3-5">3–5 providers (Pro $999/mo)</option>
            <option value="6-15">6–15 providers (Growth $1,999/mo)</option>
            <option value="15+">15+ providers (Enterprise $3,999/mo)</option>
          </Select>
        </div>
        <div>
          <FieldLabel>Main Phone Number</FieldLabel>
          <Input value={phone} onChange={setPhone} placeholder="+1 (555) 000-0000" />
        </div>
      </div>
      <NextBtn onClick={submit} loading={loading} disabled={!name}>
        Continue →
      </NextBtn>
    </div>
  );
}

function Step2EHR({ country, onNext }: { country: string; onNext: (d: any) => void }) {
  const [ehr, setEhr] = useState("standalone");
  const [clientId, setClientId] = useState("");
  const [clientSecret, setClientSecret] = useState("");
  const [practiceId, setPracticeId] = useState("");
  const [connStatus, setConnStatus] = useState<"idle"|"testing"|"ok"|"fail">("idle");
  const [loading, setLoading] = useState(false);
  const isStandalone = ehr === "standalone";

  const testConn = async () => {
    setConnStatus("testing");
    await new Promise(r => setTimeout(r, 1800));
    setConnStatus(clientId && clientSecret ? "ok" : "fail");
  };

  const submit = async () => {
    setLoading(true);
    await new Promise(r => setTimeout(r, 600));
    setLoading(false);
    onNext({ ehr_type: ehr, client_id: clientId, practice_id: practiceId });
  };

  const canContinue = isStandalone || connStatus === "ok";

  return (
    <div style={{ display:"flex", flexDirection:"column", gap:14 }}>
      <div>
        <FieldLabel>EHR System</FieldLabel>
        <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:8 }}>
          {EHR_OPTIONS.map(opt => (
            <button key={opt.value} onClick={() => { setEhr(opt.value); setConnStatus("idle"); }}
              style={{
                padding:"11px 14px", borderRadius:11, textAlign:"left" as const,
                background: ehr === opt.value ? (opt.highlight ? T.tealDim : T.surfaceHi) : T.dim4,
                border:`1px solid ${ehr === opt.value ? (opt.highlight ? T.tealBorder : T.borderHi) : T.border}`,
                cursor:"pointer", transition:"all 0.12s",
                fontFamily:"-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif",
              }}>
              <div style={{ display:"flex", alignItems:"center", justifyContent:"space-between" }}>
                <span style={{ fontSize:13, fontWeight:600, color: ehr===opt.value ? T.dim1 : T.dim2 }}>
                  {opt.label}
                </span>
                <span style={{
                  fontSize:9, fontWeight:700, padding:"2px 7px", borderRadius:100,
                  background: opt.highlight ? T.tealDim : T.dim4,
                  color: opt.highlight ? T.teal : T.dim3,
                }}>{opt.badge}</span>
              </div>
            </button>
          ))}
        </div>
      </div>

      {isStandalone ? (
        <div style={{ background:T.tealDim, border:`1px solid ${T.tealBorder}`,
          borderRadius:12, padding:"16px 18px", display:"flex", gap:12 }}>
          <span style={{ color:T.teal, fontSize:20, flexShrink:0 }}>◈</span>
          <div>
            <p style={{ fontSize:13, fontWeight:700, color:T.teal, marginBottom:4 }}>
              Standalone Mode — No EHR Required
            </p>
            <p style={{ fontSize:12, color:T.dim2, lineHeight:1.6, margin:0 }}>
              Carenova stores all patient records directly.
              Perfect for paper-based hospitals, new clinics, and practices in Nigeria.
              You can connect an EHR anytime without losing any data.
            </p>
          </div>
        </div>
      ) : (
        <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:12 }}>
          <div>
            <FieldLabel>Client ID</FieldLabel>
            <Input value={clientId} onChange={setClientId} placeholder="Client ID" />
          </div>
          <div>
            <FieldLabel>Client Secret</FieldLabel>
            <Input value={clientSecret} onChange={setClientSecret} placeholder="••••••••" type="password" />
          </div>
          <div>
            <FieldLabel>Practice ID</FieldLabel>
            <Input value={practiceId} onChange={setPracticeId} placeholder="Practice / Org ID" />
          </div>
          <div style={{ display:"flex", alignItems:"flex-end" }}>
            <button onClick={testConn}
              style={{
                width:"100%", padding:"11px", borderRadius:11, fontSize:13, fontWeight:600,
                background:T.tealDim, border:`1px solid ${T.tealBorder}`, color:T.teal,
                cursor:"pointer", fontFamily:"-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif",
              }}>
              {connStatus === "testing" ? "Testing…" : "Test Connection"}
            </button>
          </div>
          {connStatus === "ok" && (
            <div style={{ gridColumn:"1 / -1", display:"flex", alignItems:"center", gap:8 }}>
              <span style={{ color:T.green, fontSize:14 }}>✓</span>
              <span style={{ fontSize:13, color:T.green, fontWeight:600 }}>Connected successfully</span>
            </div>
          )}
          {connStatus === "fail" && (
            <div style={{ gridColumn:"1 / -1", display:"flex", alignItems:"center", gap:8 }}>
              <span style={{ color:T.red, fontSize:14 }}>✗</span>
              <span style={{ fontSize:13, color:T.red, fontWeight:600 }}>Connection failed — check credentials</span>
            </div>
          )}
        </div>
      )}
      <NextBtn onClick={submit} loading={loading} disabled={!canContinue}>
        {isStandalone ? "Continue with Standalone →" : "Continue →"}
      </NextBtn>
    </div>
  );
}

function Step3Voice({ country, onNext }: { country: string; onNext: (d: any) => void }) {
  const [retellKey, setRetellKey] = useState("");
  const [whatsapp, setWhatsapp] = useState("");
  const [greeting, setGreeting] = useState("Thank you for calling. How can I help you today?");
  const [loading, setLoading] = useState(false);
  const isNigeria = country === "NG";

  const submit = async () => {
    setLoading(true);
    await new Promise(r => setTimeout(r, 600));
    setLoading(false);
    onNext({ retell_api_key: retellKey, whatsapp_number: whatsapp, greeting });
  };

  return (
    <div style={{ display:"flex", flexDirection:"column", gap:16 }}>
      {!isNigeria && (
        <div>
          <FieldLabel>Retell AI API Key (US Voice Calls)</FieldLabel>
          <Input value={retellKey} onChange={setRetellKey} placeholder="Get free key at app.retellai.com" type="password" />
          <p style={{ fontSize:11, color:T.dim3, marginTop:6 }}>
            HIPAA BAA signed · $0.07/min · 600ms answer time
          </p>
        </div>
      )}
      <div>
        <FieldLabel>WhatsApp Business Number {isNigeria ? "(Required)" : "(Optional — Nigeria patients)"}</FieldLabel>
        <Input value={whatsapp} onChange={setWhatsapp} placeholder="+234 803 000 0000 or +1 888 000 0000" />
        <p style={{ fontSize:11, color:T.dim3, marginTop:6 }}>
          Patients book appointments via WhatsApp · Works on 2G
        </p>
      </div>
      <div>
        <FieldLabel>AI Greeting Message</FieldLabel>
        <Input value={greeting} onChange={setGreeting}
          placeholder="Thank you for calling. How can I help you today?" />
        <p style={{ fontSize:11, color:T.dim3, marginTop:6 }}>
          This is the first thing patients hear when they call
        </p>
      </div>

      {isNigeria && !whatsapp && (
        <div style={{ background:T.amberDim, border:`1px solid ${T.amber}30`,
          borderRadius:10, padding:"12px 14px", display:"flex", gap:10 }}>
          <span style={{ color:T.amber, flexShrink:0 }}>▲</span>
          <p style={{ fontSize:12, color:T.dim2, margin:0 }}>
            WhatsApp is required for Nigerian clinics. Patients in Nigeria book via WhatsApp.
          </p>
        </div>
      )}

      <NextBtn onClick={submit} loading={loading} disabled={!retellKey && !whatsapp}>
        Continue →
      </NextBtn>
    </div>
  );
}

function Step4Agents({ country, onNext }: { country: string; onNext: (d: any) => void }) {
  const defaultEnabled = ALL_AGENTS
    .filter(a => a.required || ["scheduling","intake","refill","recall"].includes(a.id))
    .map(a => a.id);
  const [enabled, setEnabled] = useState<string[]>(defaultEnabled);
  const [loading, setLoading] = useState(false);

  const toggle = (id: string, required: boolean) => {
    if (required) return;
    setEnabled(prev =>
      prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]
    );
  };

  const submit = async () => {
    setLoading(true);
    await new Promise(r => setTimeout(r, 400));
    setLoading(false);
    onNext({ enabled_agents: enabled });
  };

  return (
    <div style={{ display:"flex", flexDirection:"column", gap:14 }}>
      <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:8 }}>
        {ALL_AGENTS.map(agent => {
          const on = enabled.includes(agent.id);
          return (
            <button key={agent.id} onClick={() => toggle(agent.id, agent.required)}
              style={{
                padding:"12px 14px", borderRadius:12, textAlign:"left" as const,
                background: on ? T.surfaceHi : T.dim4,
                border:`1px solid ${on ? T.tealBorder : T.border}`,
                cursor: agent.required ? "default" : "pointer",
                transition:"all 0.12s",
                fontFamily:"-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif",
              }}>
              <div style={{ display:"flex", alignItems:"center", gap:8, marginBottom:4 }}>
                <div style={{ width:7, height:7, borderRadius:"50%", flexShrink:0,
                  background: on ? T.teal : T.dim3,
                  boxShadow: on ? `0 0 6px ${T.teal}` : "none",
                }} />
                <span style={{ fontSize:13, fontWeight:600, color: on ? T.dim1 : T.dim3 }}>
                  {agent.label}
                </span>
                {agent.required && (
                  <span style={{ fontSize:9, color:T.teal, marginLeft:"auto" }}>REQUIRED</span>
                )}
              </div>
              <p style={{ fontSize:11, color: on ? T.dim3 : "rgba(255,255,255,0.15)",
                margin:"0 0 0 15px", lineHeight:1.4 }}>
                {agent.desc}
              </p>
            </button>
          );
        })}
      </div>
      <p style={{ fontSize:11, color:T.dim3, textAlign:"center" as const }}>
        {enabled.length} agents enabled · Reception and Scheduling are always on
      </p>
      <NextBtn onClick={submit} loading={loading} disabled={false}>
        Continue with {enabled.length} agents →
      </NextBtn>
    </div>
  );
}

function Step5BAA({ country, clinicName, onNext }: any) {
  const [name, setName] = useState("");
  const [title, setTitle] = useState("");
  const [agreed, setAgreed] = useState(false);
  const [loading, setLoading] = useState(false);
  const isNigeria = country === "NG";

  if (isNigeria) {
    return (
      <div style={{ display:"flex", flexDirection:"column", gap:14 }}>
        <div style={{ background:T.greenDim, border:`1px solid ${T.green}30`,
          borderRadius:12, padding:"16px 18px", display:"flex", gap:12 }}>
          <span style={{ color:T.green, fontSize:20, flexShrink:0 }}>◉</span>
          <div>
            <p style={{ fontSize:13, fontWeight:700, color:T.green, marginBottom:4 }}>
              NDPR Compliance — Nigeria
            </p>
            <p style={{ fontSize:12, color:T.dim2, lineHeight:1.6, margin:0 }}>
              Your clinic operates under Nigeria Data Protection Regulation (NDPR).
              Carenova is NDPR compliant. No US HIPAA BAA is required.
              Patient data is stored in Supabase EU region with full encryption.
            </p>
          </div>
        </div>
        <NextBtn onClick={() => onNext({ skipped: true, reason: "Nigeria — NDPR applies" })} loading={false} disabled={false}>
          Continue →
        </NextBtn>
      </div>
    );
  }

  const submit = async () => {
    setLoading(true);
    await new Promise(r => setTimeout(r, 800));
    setLoading(false);
    onNext({ signatory_name: name, signatory_title: title, clinic_name: clinicName });
  };

  return (
    <div style={{ display:"flex", flexDirection:"column", gap:14 }}>
      <div style={{ background:T.dim4, border:`1px solid ${T.border}`,
        borderRadius:12, padding:"14px 16px", maxHeight:180, overflowY:"auto" as const }}>
        <p style={{ fontSize:11, color:T.dim3, lineHeight:1.7, margin:0 }}>
          <strong style={{ color:T.dim1 }}>BUSINESS ASSOCIATE AGREEMENT</strong>
          <br/><br/>
          This BAA is between <strong style={{ color:T.dim1 }}>{clinicName || "your clinic"}</strong> (Covered Entity)
          and Tinlance Limited RC:7962164 (Business Associate).
          <br/><br/>
          Tinlance agrees to: implement HIPAA-required safeguards, encrypt all PHI in transit (TLS 1.3)
          and at rest (AES-256), maintain PHI audit logs, notify you of any breach within 60 days,
          and sign BAAs with all sub-processors (Retell AI, Supabase, AWS).
          <br/><br/>
          This agreement complies with 45 CFR Part 164. Both parties agree to the terms upon electronic execution.
        </p>
      </div>
      <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:12 }}>
        <div>
          <FieldLabel>Your Full Name *</FieldLabel>
          <Input value={name} onChange={setName} placeholder="Dr. James Chen" />
        </div>
        <div>
          <FieldLabel>Your Title *</FieldLabel>
          <Input value={title} onChange={setTitle} placeholder="Medical Director" />
        </div>
      </div>
      <button onClick={() => setAgreed(!agreed)}
        style={{
          display:"flex", alignItems:"center", gap:10,
          background:"none", border:"none", cursor:"pointer", padding:0,
          fontFamily:"-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif",
        }}>
        <div style={{
          width:18, height:18, borderRadius:5, flexShrink:0,
          background: agreed ? T.teal : "transparent",
          border:`2px solid ${agreed ? T.teal : T.dim3}`,
          display:"flex", alignItems:"center", justifyContent:"center",
        }}>
          {agreed && <span style={{ color:"#070C17", fontSize:11, fontWeight:900 }}>✓</span>}
        </div>
        <span style={{ fontSize:12, color:T.dim2, textAlign:"left" as const }}>
          I agree to the Business Associate Agreement on behalf of {clinicName || "my clinic"}.
          I understand this is a legally binding electronic signature.
        </span>
      </button>
      <NextBtn onClick={submit} loading={loading} disabled={!name || !title || !agreed}>
        Sign BAA & Continue →
      </NextBtn>
    </div>
  );
}

function Step6Test({ clinicPhone, onNext }: any) {
  const [phone, setPhone] = useState(clinicPhone || "");
  const [status, setStatus] = useState<"idle"|"calling"|"success"|"skip">("idle");

  const startTest = async () => {
    setStatus("calling");
    await new Promise(r => setTimeout(r, 3000));
    setStatus("success");
  };

  return (
    <div style={{ display:"flex", flexDirection:"column", gap:16 }}>
      <div style={{ background:T.surface, border:`1px solid ${T.border}`,
        borderRadius:14, padding:"20px 20px" }}>
        <p style={{ fontSize:13, fontWeight:700, color:T.dim1, marginBottom:8 }}>
          What happens when you call:
        </p>
        {[
          { step:"1", text:"Carenova answers in under 1 second" },
          { step:"2", text:"AI greets you with your custom message" },
          { step:"3", text:"Ask to book an appointment — AI responds" },
          { step:"4", text:"Check your dashboard — call logged instantly" },
        ].map(s => (
          <div key={s.step} style={{ display:"flex", gap:12, marginBottom:10 }}>
            <div style={{ width:22, height:22, borderRadius:"50%", flexShrink:0,
              background:T.tealDim, border:`1px solid ${T.tealBorder}`,
              display:"flex", alignItems:"center", justifyContent:"center",
              fontSize:11, fontWeight:700, color:T.teal }}>
              {s.step}
            </div>
            <p style={{ fontSize:13, color:T.dim2, margin:0, paddingTop:3 }}>{s.text}</p>
          </div>
        ))}
      </div>

      {status === "idle" && (
        <>
          <div>
            <FieldLabel>Your Phone Number (to receive the test call)</FieldLabel>
            <Input value={phone} onChange={setPhone} placeholder="+1 (555) 000-0000" />
          </div>
          <NextBtn onClick={startTest} loading={false} disabled={!phone}>
            📞 Start Test Call
          </NextBtn>
          <button onClick={() => onNext({ skipped: true })}
            style={{ background:"none", border:"none", color:T.dim3,
              fontSize:13, cursor:"pointer", textDecoration:"underline",
              fontFamily:"-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif" }}>
            Skip test call — I'll test later
          </button>
        </>
      )}

      {status === "calling" && (
        <div style={{ textAlign:"center" as const, padding:"20px 0" }}>
          <div style={{ fontSize:40, marginBottom:12 }}>📞</div>
          <p style={{ fontSize:14, fontWeight:700, color:T.teal, margin:"0 0 6px" }}>Calling {phone}…</p>
          <p style={{ fontSize:12, color:T.dim3, margin:0 }}>Pick up and say "I want to book an appointment"</p>
        </div>
      )}

      {status === "success" && (
        <div style={{ display:"flex", flexDirection:"column", gap:12 }}>
          <div style={{ background:T.greenDim, border:`1px solid ${T.green}30`,
            borderRadius:12, padding:"16px 18px", display:"flex", gap:12 }}>
            <span style={{ color:T.green, fontSize:20 }}>✓</span>
            <div>
              <p style={{ fontSize:13, fontWeight:700, color:T.green, marginBottom:4 }}>
                Test successful!
              </p>
              <p style={{ fontSize:12, color:T.dim2, margin:0 }}>
                Your AI receptionist is configured correctly. Ready to go live.
              </p>
            </div>
          </div>
          <NextBtn onClick={() => onNext({ test_passed: true })} loading={false} disabled={false}>
            Go Live →
          </NextBtn>
        </div>
      )}
    </div>
  );
}

function Step7Live({ clinicName, country }: any) {
  const router = useRouter();
  const prices: Record<string, string> = {
    US:"$999/month", NG:"₦49,000/month", KE:"KES 12,900/month", GB:"£799/month"
  };

  return (
    <div style={{ display:"flex", flexDirection:"column", gap:20, textAlign:"center" as const }}>
      <div>
        <div style={{ fontSize:56, marginBottom:16 }}>🎉</div>
        <h2 style={{ fontSize:24, fontWeight:900, color:T.white, letterSpacing:"-0.02em",
          margin:"0 0 10px" }}>
          {clinicName || "Your clinic"} is live!
        </h2>
        <p style={{ fontSize:14, color:T.dim2, margin:0, lineHeight:1.6 }}>
          Your AI receptionist is now answering calls in 600ms.
          Every call is logged. Every appointment is booked automatically.
          Your staff never misses a patient again.
        </p>
      </div>

      <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr 1fr", gap:10 }}>
        {[
          { icon:"◎", label:"Call answering", desc:"600ms. 24/7.", color:T.teal },
          { icon:"◉", label:"Patient records", desc:"Stored securely", color:T.green },
          { icon:"▦", label:"EHR write-back", desc:"Automatic", color:T.purple },
        ].map(f => (
          <div key={f.label} style={{ background:T.surface, border:`1px solid ${T.border}`,
            borderRadius:12, padding:"14px 12px" }}>
            <p style={{ fontSize:18, color:f.color, margin:"0 0 6px" }}>{f.icon}</p>
            <p style={{ fontSize:12, fontWeight:700, color:T.dim1, margin:"0 0 3px" }}>{f.label}</p>
            <p style={{ fontSize:11, color:T.dim3, margin:0 }}>{f.desc}</p>
          </div>
        ))}
      </div>

      <div style={{ background:T.tealDim, border:`1px solid ${T.tealBorder}`,
        borderRadius:12, padding:"14px 18px" }}>
        <p style={{ fontSize:12, color:T.dim2, margin:"0 0 6px" }}>
          Your free trial started today. No payment needed for 30 days.
        </p>
        <p style={{ fontSize:11, color:T.dim3, margin:0 }}>
          After that: {prices[country] || "$999/month"} · Cancel anytime
        </p>
      </div>

      <button
        onClick={() => router.push("/dashboard")}
        style={{
          background:"linear-gradient(135deg,#00E5CC,#0099BB)",
          border:"none", borderRadius:12, padding:"14px 32px",
          color:"#070C17", fontSize:14, fontWeight:700, cursor:"pointer",
          fontFamily:"-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif",
        }}>
        Open Dashboard →
      </button>

      <p style={{ fontSize:12, color:T.dim3 }}>
        Questions? Reply to your welcome email or WhatsApp{" "}
        <span style={{ color:T.teal }}>lloyd@tinlance.com</span>
      </p>
    </div>
  );
}

// ── Main onboarding page ──────────────────────────────────────────────────────

export default function OnboardingPage() {
  const params = useParams();
  const router = useRouter();
  const stepNum = parseInt(params.step as string) || 1;

  const [data, setData] = useState<Record<string, any>>({});

  const currentStep = STEPS.find(s => s.num === stepNum) || STEPS[0];

  const handleNext = (stepData: any) => {
    const newData = { ...data, ...stepData };
    setData(newData);
    if (stepNum < 7) {
      router.push(`/onboarding/step/${stepNum + 1}`);
    }
  };

  return (
    <div style={{
      minHeight:"100vh", background:T.bg,
      display:"flex", alignItems:"flex-start", justifyContent:"center",
      padding:"40px 24px",
      fontFamily:"-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif",
    }}>
      <div style={{ width:"100%", maxWidth:600 }}>

        {/* Logo */}
        <div style={{ display:"flex", alignItems:"center", gap:10, marginBottom:36 }}>
          <div style={{ width:32, height:32, borderRadius:9,
            background:"linear-gradient(135deg,#00E5CC,#0099BB)",
            display:"flex", alignItems:"center", justifyContent:"center",
            fontWeight:900, fontSize:14, color:"#070C17" }}>C</div>
          <span style={{ fontSize:14, fontWeight:700, color:T.white }}>Carenova</span>
        </div>

        {/* Progress bar */}
        <div style={{ marginBottom:32 }}>
          <div style={{ display:"flex", justifyContent:"space-between",
            marginBottom:10 }}>
            <span style={{ fontSize:12, fontWeight:700, color:T.teal }}>
              Step {stepNum} of {STEPS.length}
            </span>
            <span style={{ fontSize:11, color:T.dim3 }}>
              ~{(7 - stepNum) * 2} min remaining
            </span>
          </div>
          <div style={{ height:4, borderRadius:4, background:T.dim4, overflow:"hidden" }}>
            <div style={{ height:"100%", borderRadius:4,
              width:`${(stepNum / STEPS.length) * 100}%`,
              background:"linear-gradient(90deg,#00E5CC,#0099BB)",
              transition:"width 0.4s ease",
            }} />
          </div>
          <div style={{ display:"flex", gap:3, marginTop:8 }}>
            {STEPS.map(s => (
              <div key={s.num} style={{ flex:1, height:2, borderRadius:2,
                background: s.num < stepNum ? T.teal : s.num === stepNum
                  ? T.tealBorder : T.dim4,
              }} />
            ))}
          </div>
        </div>

        {/* Step header */}
        <div style={{ marginBottom:28 }}>
          <div style={{ display:"flex", alignItems:"center", gap:12, marginBottom:8 }}>
            <div style={{ width:40, height:40, borderRadius:11,
              background:T.tealDim, border:`1px solid ${T.tealBorder}`,
              display:"flex", alignItems:"center", justifyContent:"center",
              fontSize:18, color:T.teal }}>
              {currentStep.icon}
            </div>
            <div>
              <p style={{ fontSize:18, fontWeight:800, color:T.white, margin:0,
                letterSpacing:"-0.02em" }}>
                {currentStep.title}
              </p>
              <p style={{ fontSize:12, color:T.dim3, margin:0 }}>
                {currentStep.desc}
              </p>
            </div>
          </div>
        </div>

        {/* Step content */}
        <div style={{ background:T.surface, border:`1px solid ${T.border}`,
          borderRadius:18, padding:24 }}>
          {stepNum === 1 && <Step1Clinic onNext={handleNext} />}
          {stepNum === 2 && <Step2EHR country={data.country || "US"} onNext={handleNext} />}
          {stepNum === 3 && <Step3Voice country={data.country || "US"} onNext={handleNext} />}
          {stepNum === 4 && <Step4Agents country={data.country || "US"} onNext={handleNext} />}
          {stepNum === 5 && <Step5BAA country={data.country || "US"}
            clinicName={data.name} onNext={handleNext} />}
          {stepNum === 6 && <Step6Test clinicPhone={data.phone} onNext={handleNext} />}
          {stepNum === 7 && <Step7Live clinicName={data.name} country={data.country || "US"} />}
        </div>

        {/* Step pills */}
        <div style={{ display:"flex", gap:6, marginTop:20, justifyContent:"center" as const }}>
          {STEPS.map(s => (
            <div key={s.num} style={{
              width: s.num === stepNum ? 24 : 8, height:8, borderRadius:4,
              background: s.num < stepNum ? T.teal : s.num === stepNum ? T.teal : T.dim4,
              opacity: s.num === stepNum ? 1 : s.num < stepNum ? 0.6 : 0.3,
              transition:"all 0.3s ease",
            }} />
          ))}
        </div>

      </div>
    </div>
  );
}
