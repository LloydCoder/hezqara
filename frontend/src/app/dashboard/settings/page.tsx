"use client";
import { useState } from "react";

const T = {
  bg: "#0B1120", surface: "#0F1729", border: "rgba(255,255,255,0.07)",
  teal: "#00E5CC", tealDim: "rgba(0,229,204,0.12)", tealBorder: "rgba(0,229,204,0.2)",
  white: "#FFFFFF", dim1: "rgba(255,255,255,0.7)", dim2: "rgba(255,255,255,0.4)",
  dim3: "rgba(255,255,255,0.18)", dim4: "rgba(255,255,255,0.07)",
  amber: "#F5A623", green: "#34D399", red: "#FF4D6A",
};

const EHR_OPTIONS = [
  { value: "standalone",    label: "Standalone (No EHR)",   badge: "Global" },
  { value: "athenahealth",  label: "athenahealth",          badge: "US" },
  { value: "modmed",        label: "ModMed EMA",            badge: "Specialty" },
  { value: "epic",          label: "Epic SMART on FHIR",    badge: "Enterprise" },
  { value: "eclinicalworks",label: "eClinicalWorks",        badge: "US" },
  { value: "nextgen",       label: "NextGen",               badge: "US" },
  { value: "drchrono",      label: "DrChrono",              badge: "US" },
  { value: "elation",       label: "Elation Health",        badge: "US" },
  { value: "tebra",         label: "Tebra (Kareo)",         badge: "US" },
  { value: "helium_health", label: "Helium Health",         badge: "Nigeria" },
  { value: "cerner",        label: "Cerner (Oracle Health)", badge: "Enterprise" },
  { value: "openmrs",       label: "OpenMRS",               badge: "Africa/Global" },
];

function Field({ label, value, placeholder, type = "text", onChange }:
  { label: string; value: string; placeholder?: string; type?: string; onChange: (v: string) => void }) {
  return (
    <div>
      <label className="block text-[11px] font-semibold tracking-[0.08em] uppercase mb-1.5"
        style={{ color: T.dim3 }}>{label}</label>
      <input type={type} value={value} onChange={e => onChange(e.target.value)}
        placeholder={placeholder}
        className="w-full rounded-xl px-4 py-2.5 text-sm outline-none transition-all"
        style={{
          background: T.dim4, border: `1px solid ${T.border}`,
          color: T.dim1,
        }} />
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-2xl p-6 space-y-4"
      style={{ background: T.surface, border: `1px solid ${T.border}` }}>
      <p className="text-sm font-bold" style={{ color: T.dim1 }}>{title}</p>
      {children}
    </div>
  );
}

export default function SettingsPage() {
  const [ehr, setEhr] = useState("athenahealth");
  const [clientId, setClientId] = useState("");
  const [clientSecret, setClientSecret] = useState("");
  const [practiceId, setPracticeId] = useState("");
  const [practicePrefix, setPracticePrefix] = useState("");
  const [apiKey, setApiKey] = useState("");
  const [connStatus, setConnStatus] = useState<"idle"|"testing"|"ok"|"fail">("idle");
  const [clinicName, setClinicName] = useState("Family Care Associates");
  const [phone, setPhone] = useState("+1 (888) 555-0001");
  const [timezone, setTimezone] = useState("America/New_York");
  const [country, setCountry] = useState("US");
  const [retellKey, setRetellKey] = useState("");
  const [whatsapp, setWhatsapp] = useState("");

  const testConnection = async () => {
    setConnStatus("testing");
    await new Promise(r => setTimeout(r, 1800));
    setConnStatus(clientId && clientSecret ? "ok" : "fail");
  };

  const isModMed = ehr === "modmed";
  const isStandalone = ehr === "standalone";

  return (
    <div className="min-h-screen p-6 space-y-5" style={{ background: T.bg }}>
      <div>
        <h1 className="text-xl font-black tracking-tight" style={{ color: T.white }}>Settings</h1>
        <p className="text-sm mt-0.5" style={{ color: T.dim3 }}>Clinic configuration and integrations</p>
      </div>

      {/* Clinic info */}
      <Section title="Clinic Details">
        <div className="grid grid-cols-2 gap-4">
          <Field label="Clinic name" value={clinicName} onChange={setClinicName} placeholder="Family Care Associates" />
          <Field label="Country" value={country} onChange={setCountry} placeholder="US" />
          <Field label="Phone number" value={phone} onChange={setPhone} placeholder="+1 (888) 555-0001" />
          <Field label="Timezone" value={timezone} onChange={setTimezone} placeholder="America/New_York" />
        </div>
      </Section>

      {/* EHR connection */}
      <Section title="EHR Connection">
        <div>
          <label className="block text-[11px] font-semibold tracking-[0.08em] uppercase mb-1.5"
            style={{ color: T.dim3 }}>EHR System</label>
          <select value={ehr} onChange={e => { setEhr(e.target.value); setConnStatus("idle"); }}
            className="w-full rounded-xl px-4 py-2.5 text-sm outline-none"
            style={{ background: T.dim4, border: `1px solid ${T.border}`, color: T.dim1 }}>
            {EHR_OPTIONS.map(o => (
              <option key={o.value} value={o.value}
                style={{ background: "#0F1729" }}>
                {o.label} — {o.badge}
              </option>
            ))}
          </select>
        </div>

        {isStandalone ? (
          <div className="rounded-xl px-4 py-4 flex items-start gap-3"
            style={{ background: T.tealDim, border: `1px solid ${T.tealBorder}` }}>
            <span style={{ color: T.teal, fontSize: 18 }}>◈</span>
            <div>
              <p className="text-sm font-semibold" style={{ color: T.teal }}>
                Standalone Mode Active
              </p>
              <p className="text-xs mt-0.5" style={{ color: T.dim2 }}>
                Carenova stores all patient records directly. No EHR required.
                Works globally — perfect for paper-based and new clinics.
                You can connect an EHR anytime without losing any data.
              </p>
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-2 gap-4">
            <Field label="Client ID" value={clientId} onChange={setClientId}
              placeholder={`${ehr} client ID`} />
            <Field label="Client Secret" value={clientSecret} onChange={setClientSecret}
              placeholder="••••••••••••" type="password" />
            {isModMed ? (
              <>
                <Field label="Practice Prefix" value={practicePrefix} onChange={setPracticePrefix}
                  placeholder="e.g. dermassoc" />
                <Field label="API Key" value={apiKey} onChange={setApiKey}
                  placeholder="x-api-key value" type="password" />
              </>
            ) : (
              <Field label="Practice ID" value={practiceId} onChange={setPracticeId}
                placeholder="Practice / Organisation ID" />
            )}
          </div>
        )}

        {!isStandalone && (
          <div className="flex items-center gap-3">
            <button onClick={testConnection}
              disabled={connStatus === "testing"}
              className="px-5 py-2.5 rounded-xl text-sm font-semibold transition-all"
              style={{
                background: connStatus === "testing" ? T.dim4 : T.tealDim,
                border: `1px solid ${connStatus === "testing" ? T.border : T.tealBorder}`,
                color: connStatus === "testing" ? T.dim3 : T.teal,
                cursor: connStatus === "testing" ? "not-allowed" : "pointer",
              }}>
              {connStatus === "testing" ? "Testing…" : "Test Connection"}
            </button>
            {connStatus === "ok" && (
              <span className="text-sm font-semibold flex items-center gap-1.5"
                style={{ color: T.green }}>
                <span>✓</span> Connected
              </span>
            )}
            {connStatus === "fail" && (
              <span className="text-sm font-semibold flex items-center gap-1.5"
                style={{ color: T.red }}>
                <span>✗</span> Connection failed — check credentials
              </span>
            )}
          </div>
        )}
      </Section>

      {/* Voice */}
      <Section title="Voice & Messaging">
        <div className="grid grid-cols-2 gap-4">
          <Field label="Retell AI API Key" value={retellKey} onChange={setRetellKey}
            placeholder="Retell AI key (US voice)" type="password" />
          <Field label="WhatsApp Business Number" value={whatsapp} onChange={setWhatsapp}
            placeholder="+234... (Nigeria)" />
        </div>
        <div className="rounded-xl px-4 py-3 flex items-center gap-3"
          style={{ background: T.dim4, border: `1px solid ${T.border}` }}>
          <span style={{ color: T.amber, fontSize: 14 }}>▲</span>
          <p className="text-xs" style={{ color: T.dim2 }}>
            Sign the Retell AI HIPAA BAA before going live with US patients.
            <span className="ml-1 underline cursor-pointer" style={{ color: T.teal }}>
              Sign BAA →
            </span>
          </p>
        </div>
      </Section>

      {/* Save */}
      <div className="flex justify-end">
        <button className="px-8 py-3 rounded-xl text-sm font-bold transition-all"
          style={{
            background: "linear-gradient(135deg, #00E5CC, #0099BB)",
            color: "#070C17",
          }}>
          Save Changes
        </button>
      </div>
    </div>
  );
}
