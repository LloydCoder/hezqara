import type { InputHTMLAttributes, ReactNode, SelectHTMLAttributes, TextareaHTMLAttributes } from "react";
import { cn } from "@/lib/cn";

export function FormField({ label, htmlFor, required, hint, error, children }: { label: string; htmlFor: string; required?: boolean; hint?: string; error?: string; children: ReactNode }) {
  const hintId = hint ? `${htmlFor}-hint` : undefined;
  const errorId = error ? `${htmlFor}-error` : undefined;
  return <div className="space-y-2"><label htmlFor={htmlFor} className="block text-sm font-semibold text-slate-800">{label}{required ? <span aria-hidden="true"> <span className="text-rose-700">*</span></span> : null}{required ? <span className="sr-only"> required</span> : null}</label>{children}{hint ? <p id={hintId} className="text-xs leading-5 text-slate-500">{hint}</p> : null}{error ? <p id={errorId} role="alert" className="text-sm text-rose-700">{error}</p> : null}</div>;
}

const field = "min-h-11 w-full rounded-lg border border-slate-300 bg-white px-3.5 py-2.5 text-sm text-slate-900 shadow-sm outline-none transition placeholder:text-slate-400 focus:border-slate-600 focus:ring-2 focus:ring-slate-200 disabled:bg-slate-100 disabled:text-slate-500";

export function Input(props: InputHTMLAttributes<HTMLInputElement>) { return <input className={cn(field, props.className)} {...props} />; }
export function Textarea(props: TextareaHTMLAttributes<HTMLTextAreaElement>) { return <textarea className={cn(field, "min-h-28", props.className)} {...props} />; }
export function Select(props: SelectHTMLAttributes<HTMLSelectElement>) { return <select className={cn(field, props.className)} {...props} />; }
export function SearchInput({ label = "Search", ...props }: InputHTMLAttributes<HTMLInputElement> & { label?: string }) { return <label className="relative block"><span className="sr-only">{label}</span><input type="search" aria-label={label} className={cn(field, "pl-10")} {...props} /><span aria-hidden="true" className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-400">⌕</span></label>; }
export function FieldHint({ children }: { children: ReactNode }) { return <p className="text-xs leading-5 text-slate-500">{children}</p>; }
export function FieldError({ children }: { children: ReactNode }) { return <p role="alert" className="text-sm text-rose-700">{children}</p>; }
