import type { ButtonHTMLAttributes, HTMLAttributes, ReactNode } from "react";
import Link from "next/link";
import { cn } from "@/lib/cn";
import type { StatusTone } from "@/types/ui";

const toneClasses: Record<StatusTone, string> = {
  success: "border-emerald-200 bg-emerald-50 text-emerald-800",
  warning: "border-amber-200 bg-amber-50 text-amber-800",
  danger: "border-rose-200 bg-rose-50 text-rose-800",
  info: "border-sky-200 bg-sky-50 text-sky-800",
  neutral: "border-slate-200 bg-slate-50 text-slate-700",
  pending: "border-indigo-200 bg-indigo-50 text-indigo-800",
};

export function Button({ className, variant = "primary", ...props }: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: "primary" | "secondary" | "ghost" | "danger" }) {
  const variants = {
    primary: "bg-slate-950 text-white hover:bg-slate-800 disabled:bg-slate-300",
    secondary: "border border-slate-200 bg-white text-slate-800 hover:bg-slate-50 disabled:text-slate-400",
    ghost: "text-slate-700 hover:bg-slate-100 disabled:text-slate-400",
    danger: "bg-rose-700 text-white hover:bg-rose-800 disabled:bg-slate-300",
  };
  return <button className={cn("inline-flex min-h-11 items-center justify-center gap-2 rounded-lg px-4 py-2.5 text-sm font-semibold transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-700 focus-visible:ring-offset-2 disabled:cursor-not-allowed", variants[variant], className)} {...props} />;
}

export function LinkButton({ href, className, variant = "primary", children }: { href: string; className?: string; variant?: "primary" | "secondary" | "ghost"; children: ReactNode }) {
  const variants = { primary: "bg-slate-950 text-white hover:bg-slate-800", secondary: "border border-slate-200 bg-white text-slate-800 hover:bg-slate-50", ghost: "text-slate-700 hover:bg-slate-100" };
  return <Link href={href} className={cn("inline-flex min-h-11 items-center justify-center gap-2 rounded-lg px-4 py-2.5 text-sm font-semibold transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-700 focus-visible:ring-offset-2", variants[variant], className)}>{children}</Link>;
}

export function Card({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("rounded-xl border border-slate-200 bg-white", className)} {...props} />;
}

export function Badge({ tone = "neutral", children, className }: { tone?: StatusTone; children: ReactNode; className?: string }) {
  return <span className={cn("inline-flex min-h-7 items-center rounded-full border px-2.5 py-1 text-xs font-semibold", toneClasses[tone], className)}>{children}</span>;
}

export function StatusBadge({ tone = "neutral", label, icon = "•" }: { tone?: StatusTone; label: string; icon?: string }) {
  return <Badge tone={tone}><span aria-hidden="true" className="mr-1.5">{icon}</span><span>{label}</span></Badge>;
}

export function Metric({ label, value, detail }: { label: string; value: ReactNode; detail?: ReactNode }) {
  return <Card className="p-5"><p className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">{label}</p><p className="mt-3 text-3xl font-bold tracking-tight text-slate-950">{value}</p>{detail ? <p className="mt-2 text-xs leading-5 text-slate-500">{detail}</p> : null}</Card>;
}

export function EmptyState({ title, description, action }: { title: string; description: string; action?: ReactNode }) {
  return <div className="rounded-xl border border-dashed border-slate-300 bg-slate-50/60 p-8 text-center"><h2 className="text-base font-semibold text-slate-900">{title}</h2><p className="mx-auto mt-2 max-w-lg text-sm leading-6 text-slate-600">{description}</p>{action ? <div className="mt-5 flex justify-center">{action}</div> : null}</div>;
}

export function LoadingState({ label = "Loading" }: { label?: string }) {
  return <div role="status" aria-live="polite" className="flex items-center gap-3 rounded-xl border border-slate-200 bg-white p-5 text-sm text-slate-600"><span aria-hidden="true" className="h-4 w-4 animate-pulse rounded-full bg-slate-300" />{label}<span className="sr-only">, please wait</span></div>;
}

export function ErrorState({ title = "Something went wrong", description, onRetry }: { title?: string; description: string; onRetry?: () => void }) {
  return <div role="alert" className="rounded-xl border border-rose-200 bg-rose-50 p-5"><h2 className="font-semibold text-rose-900">{title}</h2><p className="mt-1 text-sm leading-6 text-rose-800">{description}</p>{onRetry ? <Button variant="secondary" className="mt-4" onClick={onRetry}>Try again</Button> : null}</div>;
}

export function Skeleton({ className }: { className?: string }) { return <div aria-hidden="true" className={cn("animate-pulse rounded-lg bg-slate-100", className)} />; }
