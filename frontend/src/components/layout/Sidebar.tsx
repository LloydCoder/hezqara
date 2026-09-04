"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const links = [
  ["Overview", "/dashboard"],
  ["Agents", "/dashboard/agents"],
  ["Calls", "/dashboard/calls"],
  ["Appointments", "/dashboard/appointments"],
  ["Patients", "/dashboard/patients"],
  ["Insurance", "/dashboard/insurance"],
  ["Prior auth", "/dashboard/prior-auth"],
  ["Billing", "/dashboard/billing"],
] as const;

export function Sidebar() {
  const pathname = usePathname();
  return (
    <aside className="fixed inset-y-0 left-0 z-40 hidden w-56 border-r border-white/5 bg-slate-950 px-3 py-5 lg:block">
      <div className="px-3 pb-7 text-lg font-black tracking-tight text-white">HEZQARA</div>
      <nav className="space-y-1">
        {links.map(([label, href]) => {
          const active = href === "/dashboard" ? pathname === href : pathname.startsWith(href);
          return (
            <Link key={href} href={href} className={`block rounded-lg px-3 py-2 text-sm transition ${active ? "bg-white/10 text-white" : "text-slate-400 hover:bg-white/5 hover:text-white"}`}>
              {label}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
