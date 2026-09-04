"use client";

const PLANS = [
  { id: "starter", label: "Starter", price: 499, providers: "1–2" },
  { id: "pro", label: "Pro", price: 999, providers: "3–5" },
  { id: "growth", label: "Growth", price: 1999, providers: "6–15" },
  { id: "enterprise", label: "Enterprise", price: 3999, providers: "15+" },
];

export default function BillingPage() {
  return (
    <main className="min-h-screen bg-slate-950 p-6 text-white">
      <header className="mb-6">
        <h1 className="text-2xl font-bold">Billing</h1>
        <p className="mt-1 text-sm text-slate-400">Plans and subscription management.</p>
      </header>

      <section className="mb-6 rounded-2xl border border-white/5 bg-white/[0.03] p-5">
        <h2 className="font-semibold">Subscription status</h2>
        <p className="mt-2 text-sm text-slate-400">
          Your live subscription status is provided by the billing service. This page does not invent a plan, renewal date, or invoice amount.
        </p>
      </section>

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {PLANS.map((plan) => (
          <article key={plan.id} className="rounded-2xl border border-white/5 bg-white/[0.03] p-5">
            <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">{plan.label}</p>
            <p className="mt-3 text-3xl font-black">${plan.price}<span className="text-sm font-normal text-slate-500">/mo</span></p>
            <p className="mt-1 text-xs text-slate-500">{plan.providers} providers</p>
            <button type="button" disabled className="mt-6 w-full rounded-xl border border-white/10 bg-white/5 px-4 py-2 text-sm text-slate-400">
              Billing integration required
            </button>
          </article>
        ))}
      </section>
    </main>
  );
}
