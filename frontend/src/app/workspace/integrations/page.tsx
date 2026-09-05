const providers=[
  ['FHIR / EHR','FHIR exchange, patient, coverage and appointment synchronization'],
  ['Eligibility','Coverage eligibility verification through a governed payer adapter'],
  ['Prior Authorization','CRD/DTR/PAS-ready authorization boundary'],
  ['Claims','Clearinghouse submission and acknowledgement boundary'],
  ['Payments','Provider-confirmed payment lifecycle boundary'],
  ['Messaging','Outbound/inbound messaging provider boundary'],
];
export default function IntegrationsPage(){return <main className="min-h-screen bg-slate-950 p-6 text-white"><header className="mb-8"><p className="text-xs font-semibold uppercase tracking-wider text-slate-500">Interoperability</p><h1 className="mt-2 text-3xl font-bold">Integrations</h1><p className="mt-2 max-w-3xl text-sm text-slate-400">Governed connectivity to healthcare systems. Provider configuration and verified connection health are required before live external operations.</p></header><section className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">{providers.map(([name,desc])=><article key={name} className="rounded-2xl border border-white/10 bg-white/[.03] p-5"><h2 className="font-semibold">{name}</h2><p className="mt-2 text-sm text-slate-400">{desc}</p><p className="mt-5 text-xs text-amber-300">Configuration required</p></article>)}</section><div className="mt-8 rounded-2xl border border-white/10 p-5"><h2 className="font-semibold">Truthful connection states</h2><p className="mt-2 text-sm text-slate-400">Not configured, configuration required, healthy, degraded, unavailable, authentication failed, rate limited and provider error are distinct states. Test providers are never presented as production connectivity.</p></div></main>}
