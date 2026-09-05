"use client";

import { useAnalytics } from "@/hooks/useAgents";

export default function AnalyticsPage() {
  const { summary, loading, error, reload } = useAnalytics();

  return (
    <section className="space-y-6 p-5 sm:p-8">
      <header className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-xs font-bold uppercase tracking-[0.16em] text-slate-400">Operations intelligence</p>
          <h1 className="mt-2 text-3xl font-black tracking-tight">Measured performance</h1>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-500">
            Organization-scoped metrics derived from persisted operational events. No synthetic activity or estimated financial values are displayed.
          </p>
        </div>
        <button type="button" onClick={() => void reload()} className="rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50">
          Refresh
        </button>
      </header>

      {error && <div role="alert" className="rounded-2xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">{error}</div>}

      {loading ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4" aria-label="Loading analytics">
          {[1, 2, 3, 4].map((item) => <div key={item} className="h-32 animate-pulse rounded-2xl bg-white" />)}
        </div>
      ) : summary ? (
        <>
          <div className="rounded-2xl border border-slate-200 bg-white p-4 text-xs text-slate-500">
            Reporting window: <span className="font-semibold text-slate-700">{new Date(summary.window.start).toLocaleDateString()}</span> — <span className="font-semibold text-slate-700">{new Date(summary.window.end).toLocaleDateString()}</span>. Fresh through {new Date(summary.freshness).toLocaleTimeString()}.
          </div>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {summary.metrics.map((metric) => (
              <article key={metric.key} className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
                <p className="text-xs font-bold uppercase tracking-[0.14em] text-slate-400">{metric.label}</p>
                <p className="mt-3 text-3xl font-black tabular-nums">{metric.value ?? "—"}</p>
                <p className="mt-2 text-xs leading-5 text-slate-500">{metric.definition}</p>
                <p className="mt-2 text-[11px] font-medium text-slate-400">Source: {metric.source_tables.join(", ")}</p>
              </article>
            ))}
          </div>
        </>
      ) : (
        <div className="rounded-3xl border border-dashed border-slate-300 bg-white p-10 text-center">
          <h2 className="font-bold">No analytics data available</h2>
          <p className="mx-auto mt-2 max-w-md text-sm leading-6 text-slate-500">Once organization-scoped operational events are available, this workspace will show sourced metrics with definitions and time ranges.</p>
        </div>
      )}
    </section>
  );
}
