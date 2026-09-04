import { SiteFooter, SiteHeader } from "./SiteHeader";

export function MarketingShell({ children }: { children: React.ReactNode }) {
  return <div className="min-h-screen bg-white text-slate-950"><SiteHeader />{children}<SiteFooter /></div>;
}

export function SectionIntro({ eyebrow, title, body }: { eyebrow: string; title: string; body: string }) {
  return <div className="max-w-3xl"><p className="text-xs font-bold uppercase tracking-[0.18em] text-slate-500">{eyebrow}</p><h1 className="mt-4 text-4xl font-black tracking-tight text-slate-950 sm:text-5xl">{title}</h1><p className="mt-5 text-lg leading-8 text-slate-600">{body}</p></div>;
}

export function FeatureCard({ title, body, href }: { title: string; body: string; href?: string }) {
  return <article className="rounded-2xl border border-slate-200 bg-white p-6 shadow-[0_1px_2px_rgba(15,23,42,0.04)]"><div className="mb-5 h-9 w-9 rounded-xl bg-slate-100" aria-hidden="true"/><h2 className="text-lg font-bold text-slate-950">{title}</h2><p className="mt-2 text-sm leading-6 text-slate-600">{body}</p>{href ? <a href={href} className="mt-5 inline-flex text-sm font-semibold text-slate-950 underline decoration-slate-300 underline-offset-4 hover:decoration-slate-950">Explore →</a> : null}</article>;
}

export function TrustBand() {
  return <section className="border-y border-slate-200 bg-slate-50"><div className="mx-auto max-w-7xl px-5 py-10 sm:px-8"><div className="grid gap-6 md:grid-cols-3"><div><p className="text-sm font-bold text-slate-950">Governed execution</p><p className="mt-1 text-sm text-slate-500">Permissions and policy boundaries stay explicit.</p></div><div><p className="text-sm font-bold text-slate-950">Human escalation</p><p className="mt-1 text-sm text-slate-500">Uncertainty and consequential decisions can return to people.</p></div><div><p className="text-sm font-bold text-slate-950">Auditability</p><p className="mt-1 text-sm text-slate-500">Operational actions are designed to remain observable and accountable.</p></div></div></div></section>;
}
