// Utility functions

import { type ClassValue, clsx } from "clsx";

export function cn(...inputs: ClassValue[]) {
  return clsx(inputs);
}

export function formatDuration(ms: number): string {
  const seconds = Math.floor(ms / 1000);
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = seconds % 60;
  if (minutes === 0) return `${seconds}s`;
  return `${minutes}m ${remainingSeconds}s`;
}

export function formatCurrency(usd: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  }).format(usd);
}

export function formatDate(iso: string): string {
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  }).format(new Date(iso));
}

export function formatDateTime(iso: string): string {
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
    hour12: true,
  }).format(new Date(iso));
}

export function maskPhone(phone: string): string {
  const digits = phone.replace(/\D/g, "");
  if (digits.length >= 10) {
    return `+1 (${digits.slice(-10, -7)}) ${digits.slice(-7, -4)}-****`;
  }
  return "****";
}

export function intentLabel(intent: string | null): string {
  const labels: Record<string, string> = {
    appointment: "Appointment",
    refill: "Refill",
    insurance: "Insurance",
    records: "Records",
    referral: "Referral",
    recall: "Recall",
    general: "General",
    emergency: "Emergency",
    unknown: "Unknown",
  };
  return intent ? (labels[intent] ?? intent) : "—";
}

export function agentStatusColor(status: string): string {
  const colors: Record<string, string> = {
    active: "text-emerald-600 bg-emerald-50",
    idle: "text-slate-500 bg-slate-50",
    processing: "text-blue-600 bg-blue-50",
    error: "text-red-600 bg-red-50",
    disabled: "text-slate-400 bg-slate-100",
  };
  return colors[status] ?? "text-slate-500 bg-slate-50";
}
