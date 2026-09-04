"use client";
import { useAnalytics } from "@/hooks/useAgents";

export default function AnalyticsPage() {
  const { summary, daily, loading, error } = useAnalytics("");
  const metrics = [
    ["Total calls", summary?.total_calls],
    ["Appointments booked", summary?.total_appointments_booked],
    ["Cost savings", summary?.total_cost_savings_usd == null ? undefined : `$${summary.total_cost_savings_usd.toFixed(2)}`],
  ];
  return <main style={{padding:24}}>
    <h1>Analytics</h1>
    <p>Measured HEZQARA operational data only. No synthetic metrics are displayed.</p>
    {error && <p role="alert">{error}</p>}
    {loading && <p>Loading…</p>}
    {!loading && !error && <section style={{display:"grid",gap:16,gridTemplateColumns:"repeat(3,1fr)"}}>
      {metrics.map(([label,value])=><article key={label as string}><strong>{label}</strong><div>{value == null ? "Unavailable" : value}</div></article>)}
      <article><strong>Daily metrics</strong><div>{daily ? "Available" : "Unavailable"}</div></article>
    </section>}
  </main>;
}
