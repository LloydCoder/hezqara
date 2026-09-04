"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";

const NAV_ITEMS = [
  { href: "/dashboard",              label: "Command",      icon: "⚡", group: "main" },
  { href: "/dashboard/agents",       label: "Agents",       icon: "◈",  group: "main" },
  { href: "/dashboard/calls",        label: "Calls",        icon: "◎",  group: "main" },
  { href: "/dashboard/walkin",       label: "Walk-In Queue", icon: "▣",  group: "main" },
  { href: "/dashboard/appointments", label: "Schedule",     icon: "▦",  group: "main" },
  { href: "/dashboard/patients",     label: "Patients",     icon: "◉",  group: "main" },
  { href: "/dashboard/insurance",    label: "Insurance",    icon: "◫",  group: "clinical" },
  { href: "/dashboard/prior-auth",   label: "Prior Auth",   icon: "◪",  group: "clinical" },
  { href: "/dashboard/recalls",      label: "Recalls",      icon: "◬",  group: "clinical" },
  { href: "/dashboard/referrals",    label: "Referrals",    icon: "◭",  group: "clinical" },
  { href: "/dashboard/records",      label: "Records",      icon: "◮",  group: "clinical" },
  { href: "/dashboard/analytics",    label: "Analytics",    icon: "◩",  group: "ops" },
  { href: "/dashboard/compliance",   label: "Compliance",   icon: "◈",  group: "ops" },
  { href: "/dashboard/billing",      label: "Billing",      icon: "◧",  group: "ops" },
  { href: "/dashboard/settings",     label: "Settings",     icon: "◫",  group: "ops" },
];

const GROUPS = [
  { id: "main",     label: "OPERATIONS" },
  { id: "clinical", label: "CLINICAL" },
  { id: "ops",      label: "INSIGHTS" },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="fixed inset-y-0 left-0 z-50 w-56 flex flex-col"
      style={{ background: "#070C17", borderRight: "1px solid rgba(255,255,255,0.06)" }}>

      {/* Logo */}
      <div className="px-5 py-5" style={{ borderBottom: "1px solid rgba(255,255,255,0.06)" }}>
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg flex items-center justify-center text-sm font-black"
            style={{ background: "linear-gradient(135deg, #00E5CC, #0099BB)", color: "#070C17" }}>
            C
          </div>
          <div>
            <p className="text-sm font-bold text-white tracking-tight">Carenova</p>
            <p className="text-xs" style={{ color: "rgba(255,255,255,0.3)" }}>AI Front Office</p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto py-4 px-3 space-y-5">
        {GROUPS.map((group) => {
          const items = NAV_ITEMS.filter(i => i.group === group.id);
          return (
            <div key={group.id}>
              <p className="px-2 mb-1.5 text-[10px] font-semibold tracking-[0.12em]"
                style={{ color: "rgba(255,255,255,0.2)" }}>
                {group.label}
              </p>
              <div className="space-y-0.5">
                {items.map((item) => {
                  const isActive = item.href === "/dashboard"
                    ? pathname === "/dashboard"
                    : pathname.startsWith(item.href);
                  return (
                    <Link key={item.href} href={item.href}
                      className={cn(
                        "flex items-center gap-2.5 px-2.5 py-2 rounded-lg text-sm transition-all duration-150",
                        isActive
                          ? "text-white font-medium"
                          : "hover:text-white"
                      )}
                      style={isActive
                        ? { background: "rgba(0,229,204,0.12)", color: "#00E5CC" }
                        : { color: "rgba(255,255,255,0.38)" }
                      }
                    >
                      <span className="text-xs w-4 text-center leading-none">{item.icon}</span>
                      <span className="text-[13px]">{item.label}</span>
                      {isActive && (
                        <div className="ml-auto w-1.5 h-1.5 rounded-full"
                          style={{ background: "#00E5CC" }} />
                      )}
                    </Link>
                  );
                })}
              </div>
            </div>
          );
        })}
      </nav>

      {/* Live status pill */}
      <div className="px-4 pb-4">
        <div className="rounded-lg px-3 py-2.5 flex items-center gap-2"
          style={{ background: "rgba(0,229,204,0.08)", border: "1px solid rgba(0,229,204,0.15)" }}>
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full opacity-75"
              style={{ background: "#00E5CC" }} />
            <span className="relative inline-flex rounded-full h-2 w-2"
              style={{ background: "#00E5CC" }} />
          </span>
          <span className="text-[11px] font-medium" style={{ color: "#00E5CC" }}>System Live</span>
          <span className="ml-auto text-[10px]" style={{ color: "rgba(255,255,255,0.25)" }}>HIPAA ✓</span>
        </div>
      </div>
    </aside>
  );
}
