"use client";
import { usePatients } from "@/hooks/useAgents";
import { useState } from "react";

const T = {
  bg: "#0B1120", surface: "#0F1729", border: "rgba(255,255,255,0.07)",
  teal: "#00E5CC", tealDim: "rgba(0,229,204,0.12)", tealBorder: "rgba(0,229,204,0.2)",
  white: "#FFFFFF", dim1: "rgba(255,255,255,0.7)", dim2: "rgba(255,255,255,0.4)",
  dim3: "rgba(255,255,255,0.18)", dim4: "rgba(255,255,255,0.07)",
  amber: "#F5A623",
};

const CLINIC_ID = process.env.NEXT_PUBLIC_DEMO_CLINIC_ID ?? "demo_clinic";

export default function PatientsPage() {
  const { patients, loading, search, setSearch } = usePatients(CLINIC_ID);
  const [selected, setSelected] = useState<string | null>(null);

  return (
    <div className="min-h-screen p-6 space-y-5" style={{ background: T.bg }}>
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-black tracking-tight" style={{ color: T.white }}>Patients</h1>
          <p className="text-sm mt-0.5" style={{ color: T.dim3 }}>
            {loading ? "Loading…" : `${patients.length} records`}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <input value={search} onChange={e => setSearch?.(e.target.value)}
            placeholder="Search by name or phone…"
            className="text-sm rounded-xl px-4 py-2.5 outline-none w-64"
            style={{ background: T.surface, border: `1px solid ${T.border}`, color: T.dim1 }} />
          <button className="px-5 py-2.5 rounded-xl text-sm font-semibold"
            style={{ background: T.tealDim, border: `1px solid ${T.tealBorder}`, color: T.teal }}>
            + Add Patient
          </button>
        </div>
      </div>

      <div className="rounded-2xl overflow-hidden"
        style={{ background: T.surface, border: `1px solid ${T.border}` }}>
        <table className="w-full">
          <thead>
            <tr style={{ borderBottom: `1px solid ${T.border}` }}>
              {["Patient", "Date of Birth", "Phone", "Insurance", "Status"].map(h => (
                <th key={h} className="text-left px-5 py-3.5 text-[10px] font-semibold tracking-[0.1em] uppercase"
                  style={{ color: T.dim3 }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {loading ? (
              Array.from({ length: 8 }).map((_, i) => (
                <tr key={i} style={{ borderBottom: `1px solid ${T.border}` }}>
                  {Array.from({ length: 5 }).map((_, j) => (
                    <td key={j} className="px-5 py-3.5">
                      <div className="h-4 rounded-lg animate-pulse w-24"
                        style={{ background: T.dim4 }} />
                    </td>
                  ))}
                </tr>
              ))
            ) : patients.length === 0 ? (
              <tr>
                <td colSpan={5} className="px-5 py-16 text-center">
                  <div className="flex flex-col items-center gap-3">
                    <div className="w-12 h-12 rounded-full flex items-center justify-center text-xl"
                      style={{ background: T.tealDim, border: `1px solid ${T.tealBorder}`, color: T.teal }}>
                      ◉
                    </div>
                    <p className="text-sm font-medium" style={{ color: T.dim2 }}>No patients yet</p>
                    <p className="text-xs" style={{ color: T.dim3 }}>
                      Import from CSV or wait for the first patient call
                    </p>
                  </div>
                </td>
              </tr>
            ) : (
              patients.map((p: any) => (
                <tr key={p.id}
                  onClick={() => setSelected(p.id)}
                  className="cursor-pointer transition-colors"
                  style={{
                    borderBottom: `1px solid ${T.border}`,
                    background: selected === p.id ? T.tealDim : "transparent",
                  }}>
                  <td className="px-5 py-3.5">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0"
                        style={{ background: T.tealDim, color: T.teal, border: `1px solid ${T.tealBorder}` }}>
                        {(p.first_name?.[0] ?? "?")}{(p.last_name?.[0] ?? "")}
                      </div>
                      <span className="text-sm font-semibold" style={{ color: T.dim1 }}>
                        {p.first_name} {p.last_name}
                      </span>
                    </div>
                  </td>
                  <td className="px-5 py-3.5 text-sm" style={{ color: T.dim2 }}>
                    {p.date_of_birth ?? "—"}
                  </td>
                  <td className="px-5 py-3.5 text-sm font-mono" style={{ color: T.dim2 }}>
                    {p.phone ?? "—"}
                  </td>
                  <td className="px-5 py-3.5 text-sm" style={{ color: T.dim2 }}>
                    {p.insurance_carrier ?? "Uninsured"}
                  </td>
                  <td className="px-5 py-3.5">
                    <span className="text-[11px] font-semibold px-2.5 py-1 rounded-full"
                      style={{ background: T.tealDim, color: T.teal, border: `1px solid ${T.tealBorder}` }}>
                      Active
                    </span>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
