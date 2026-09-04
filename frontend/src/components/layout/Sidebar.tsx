"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { UserButton } from "@clerk/nextjs";

const groups = [
  { title: "Operate", links: [["Command Center", "/dashboard"], ["AI Workforce", "/dashboard/agents"], ["Tasks", "/dashboard/tasks"], ["Patients", "/dashboard/patients"], ["Scheduling", "/dashboard/appointments"]] },
  { title: "Revenue & access", links: [["Billing", "/dashboard/billing"], ["Insurance", "/dashboard/insurance"], ["Prior authorization", "/dashboard/prior-auth"]] },
  { title: "Records & engagement", links: [["Records", "/dashboard/records"], ["Referrals", "/dashboard/referrals"], ["Recall", "/dashboard/recalls"], ["Calls", "/dashboard/calls"]] },
  { title: "Governance", links: [["Analytics", "/dashboard/analytics"], ["Compliance", "/dashboard/compliance"], ["Settings", "/dashboard/settings"]] },
] as const;

export function Sidebar() {
  const pathname = usePathname();
  return <>
    <aside className="fixed inset-y-0 left-0 z-40 hidden w-64 border-r border-slate-200 bg-white px-3 py-5 lg:flex lg:flex-col">
      <Link href="/dashboard" className="flex items-center gap-2 px-3 pb-7" aria-label="HEZQARA command center"><span className="flex h-8 w-8 items-center justify-center rounded-lg bg-slate-950 text-sm font-black text-white">H</span><span className="text-base font-black tracking-tight text-slate-950">HEZQARA</span></Link>
      <nav className="min-h-0 flex-1 space-y-5 overflow-y-auto" aria-label="Application navigation">{groups.map(group=><div key={group.title}><p className="px-3 text-[10px] font-bold uppercase tracking-[0.16em] text-slate-400">{group.title}</p><div className="mt-2 space-y-0.5">{group.links.map(([label,href])=>{const active=href==="/dashboard"?pathname===href:pathname.startsWith(href);return <Link key={href} href={href} className={`block rounded-lg px-3 py-2 text-sm font-medium transition ${active?"bg-slate-950 text-white":"text-slate-600 hover:bg-slate-100 hover:text-slate-950"}`}>{label}</Link>})}</div></div>)}</nav>
      <div className="mt-4 flex items-center gap-3 border-t border-slate-100 px-3 pt-4"><UserButton afterSignOutUrl="/"/><div className="text-xs text-slate-500">Signed in</div></div>
    </aside>
    <div className="sticky top-0 z-30 border-b border-slate-200 bg-white/95 px-4 py-3 backdrop-blur lg:hidden"><div className="flex items-center justify-between"><Link href="/dashboard" className="flex items-center gap-2"><span className="flex h-8 w-8 items-center justify-center rounded-lg bg-slate-950 text-sm font-black text-white">H</span><span className="font-black">HEZQARA</span></Link><UserButton afterSignOutUrl="/"/></div><nav className="mt-3 flex gap-2 overflow-x-auto pb-1" aria-label="Mobile application navigation">{groups.flatMap(g=>g.links).map(([label,href])=>{const active=href==="/dashboard"?pathname===href:pathname.startsWith(href);return <Link key={href} href={href} className={`whitespace-nowrap rounded-lg px-3 py-1.5 text-xs font-semibold ${active?"bg-slate-950 text-white":"bg-slate-100 text-slate-600"}`}>{label}</Link>})}</nav></div>
  </>;
}
