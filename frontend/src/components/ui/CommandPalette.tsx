"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { Button } from "@/components/ui/primitives";

const COMMANDS = [
  ["Command Center", "/dashboard"], ["Patients", "/dashboard/patients"], ["Scheduling", "/dashboard/appointments"],
  ["AI Workforce", "/dashboard/agents"], ["Tasks", "/dashboard/tasks"], ["AI Executions", "/dashboard/executions"],
  ["Billing", "/dashboard/billing"], ["Insurance", "/dashboard/insurance"], ["Analytics", "/dashboard/analytics"],
  ["Compliance", "/dashboard/compliance"], ["Settings", "/dashboard/settings"],
] as const;

export function CommandPalette() {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  useEffect(() => { const onKey = (event: KeyboardEvent) => { if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") { event.preventDefault(); setOpen(true); } if (event.key === "Escape") setOpen(false); }; window.addEventListener("keydown", onKey); return () => window.removeEventListener("keydown", onKey); }, []);
  const results = useMemo(() => COMMANDS.filter(([label]) => label.toLowerCase().includes(query.toLowerCase())), [query]);
  return <>
    <Button variant="secondary" className="hidden sm:inline-flex" onClick={() => setOpen(true)} aria-label="Open command palette"><span>Search</span><kbd className="rounded border border-slate-200 px-1.5 py-0.5 text-[10px] text-slate-500">⌘K</kbd></Button>
    {open ? <div className="fixed inset-0 z-50 bg-slate-950/40 p-4 sm:p-10" role="presentation" onMouseDown={(e)=>{if(e.target===e.currentTarget)setOpen(false)}}><div role="dialog" aria-modal="true" aria-labelledby="command-title" className="mx-auto mt-10 w-full max-w-xl overflow-hidden rounded-xl border border-slate-200 bg-white shadow-2xl"><div className="border-b border-slate-200 p-3"><h2 id="command-title" className="sr-only">Command palette</h2><input autoFocus value={query} onChange={(e)=>setQuery(e.target.value)} placeholder="Search destinations" aria-label="Search destinations" className="min-h-11 w-full border-0 px-2 text-sm outline-none placeholder:text-slate-400" /></div><nav aria-label="Command results" className="max-h-[60vh] overflow-y-auto p-2">{results.length ? results.map(([label,href])=><Link key={href} href={href} onClick={()=>setOpen(false)} className="block rounded-lg px-3 py-3 text-sm font-medium text-slate-800 hover:bg-slate-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-500">{label}</Link>) : <p className="p-4 text-sm text-slate-500">No matching destinations.</p>}</nav><p className="border-t border-slate-100 px-4 py-3 text-xs text-slate-500">Press Esc to close.</p></div></div> : null}
  </>;
}
