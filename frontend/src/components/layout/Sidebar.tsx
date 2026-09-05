"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { UserButton } from "@clerk/nextjs";
import { CommandPalette } from "@/components/ui/CommandPalette";

type NavItem = readonly [string, string];
type NavGroup = { title: string; links: readonly NavItem[] };

const groups: readonly NavGroup[] = [
  { title: "Operate", links: [["Command Center","/dashboard"],["AI Workforce","/dashboard/agents"],["Tasks","/dashboard/tasks"],["AI executions","/dashboard/executions"],["Patients","/dashboard/patients"],["Scheduling","/dashboard/appointments"]] },
  { title: "Revenue & access", links: [["Billing","/dashboard/billing"],["Insurance","/dashboard/insurance"],["Prior authorization","/dashboard/prior-auth"]] },
  { title: "Records & engagement", links: [["Records","/dashboard/records"],["Referrals","/dashboard/referrals"],["Recall","/dashboard/recalls"],["Calls","/dashboard/calls"]] },
  { title: "Governance", links: [["Analytics","/dashboard/analytics"],["Compliance","/dashboard/compliance"],["Settings","/dashboard/settings"]] },
];

export function Sidebar() {
  const pathname = usePathname();
  const link = ([label, href]: NavItem, mobile = false) => {
    const active = href === "/dashboard" ? pathname === href : pathname.startsWith(href);
    return <Link key={href} href={href} aria-current={active ? "page" : undefined} className={mobile ? `whitespace-nowrap rounded-lg px-3 py-2 text-xs font-semibold ${active ? "bg-slate-950 text-white" : "bg-slate-100 text-slate-700"}` : `block rounded-lg px-3 py-2.5 text-sm font-medium transition-colors ${active ? "bg-slate-950 text-white" : "text-slate-700 hover:bg-slate-100 hover:text-slate-950"}`}>{label}</Link>;
  };
  return <>
    <aside className="fixed inset-y-0 left-0 z-40 hidden w-64 border-r border-slate-200 bg-white px-3 py-5 lg:flex lg:flex-col">
      <div className="flex items-center justify-between px-3 pb-6"><Link href="/dashboard" className="flex items-center gap-2" aria-label="HEZQARA command center"><span className="grid h-8 w-8 place-items-center rounded-lg bg-slate-950 text-sm font-black text-white">H</span><span className="text-base font-black tracking-tight text-slate-950">HEZQARA</span></Link><CommandPalette /></div>
      <nav aria-label="Application navigation" className="min-h-0 flex-1 space-y-5 overflow-y-auto">{groups.map(group=><section key={group.title}><h2 className="px-3 text-[10px] font-bold uppercase tracking-[0.16em] text-slate-400">{group.title}</h2><div className="mt-2 space-y-0.5">{group.links.map(item=>link(item))}</div></section>)}</nav>
      <div className="mt-4 flex items-center gap-3 border-t border-slate-100 px-3 pt-4"><UserButton afterSignOutUrl="/"/><span className="text-xs text-slate-500">Account</span></div>
    </aside>
    <div className="sticky top-0 z-30 border-b border-slate-200 bg-white px-4 py-3 lg:hidden"><div className="flex items-center justify-between"><Link href="/dashboard" className="flex items-center gap-2" aria-label="HEZQARA command center"><span className="grid h-8 w-8 place-items-center rounded-lg bg-slate-950 text-sm font-black text-white">H</span><span className="font-black tracking-tight">HEZQARA</span></Link><div className="flex items-center gap-2"><CommandPalette /><UserButton afterSignOutUrl="/"/></div></div><nav aria-label="Mobile application navigation" className="mt-3 flex gap-2 overflow-x-auto pb-1">{groups.flatMap(group=>group.links).map(item=>link(item,true))}</nav></div>
  </>;
}
