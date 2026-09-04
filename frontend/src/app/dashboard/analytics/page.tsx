"use client";
import { useAnalytics } from "@/hooks/useAgents";
export default function AnalyticsPage(){const {summary,loading,error}=useAnalytics();return <main className="p-6"><h1>Analytics</h1><p>Measured HEZQARA operational data only. No synthetic metrics are displayed.</p>{error&&<p role="alert">{error}</p>}{loading&&<p>Loading…</p>}{!loading&&!error&&<section><p>Total calls: {summary?.total_calls??"Unavailable"}</p><p>Appointments booked: {summary?.total_appointments_booked??"Unavailable"}</p></section>}</main>}
