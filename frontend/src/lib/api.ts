import type { Agent, AgentType } from "@/types/agent";
import type { Patient, Appointment, Call } from "@/types/patient";
import type { DailyMetrics, AnalyticsSummary } from "@/types/analytics";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8004";

type TokenProvider = () => Promise<string | null>;
let tokenProvider: TokenProvider | null = null;

export function setApiTokenProvider(provider: TokenProvider | null) {
  tokenProvider = provider;
}

class APIError extends Error {
  constructor(message: string, public status: number, public data?: unknown) {
    super(message);
    this.name = "APIError";
  }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = tokenProvider ? await tokenProvider() : null;
  const headers = new Headers(options.headers);
  headers.set("Content-Type", "application/json");
  if (token) headers.set("Authorization", `Bearer ${token}`);

  const res = await fetch(`${BASE_URL}${path}`, { ...options, headers, cache: "no-store" });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new APIError(
      typeof data === "object" && data && "detail" in data ? String(data.detail) : `API error ${res.status}`,
      res.status,
      data,
    );
  }
  return res.json() as Promise<T>;
}

const q = (value: string) => encodeURIComponent(value);

export const api = {
  health: { check: () => request<{ status: string; service: string; port: number }>("/health") },
  agents: {
    list: (clinicId: string) => request<Agent[]>(`/agents?clinic_id=${q(clinicId)}`),
    get: (clinicId: string, agentType: AgentType) => request<Agent>(`/agents/${agentType}?clinic_id=${q(clinicId)}`),
    toggle: (clinicId: string, agentType: AgentType, enabled: boolean) => request<{ updated: boolean }>(`/agents/${agentType}/toggle`, { method: "POST", body: JSON.stringify({ clinic_id: clinicId, enabled }) }),
  },
  calls: {
    list: (clinicId: string, limit = 50) => request<Call[]>(`/calls?clinic_id=${q(clinicId)}&limit=${limit}`),
    get: (callId: string) => request<Call & { transcript: unknown[] }>(`/calls/${q(callId)}`),
  },
  appointments: {
    list: (clinicId: string, status?: string) => request<Appointment[]>(`/appointments?clinic_id=${q(clinicId)}${status ? `&status=${q(status)}` : ""}`),
    get: (appointmentId: string) => request<Appointment>(`/appointments/${q(appointmentId)}`),
    cancel: (appointmentId: string, reason: string) => request<{ success: boolean }>(`/appointments/${q(appointmentId)}/cancel`, { method: "POST", body: JSON.stringify({ reason }) }),
  },
  patients: {
    list: (clinicId: string, search?: string) => request<Patient[]>(`/patients?clinic_id=${q(clinicId)}${search ? `&search=${q(search)}` : ""}`),
    get: (patientId: string) => request<Patient>(`/patients/${q(patientId)}`),
  },
  analytics: {
    summary: (clinicId: string, period: "today" | "week" | "month") => request<AnalyticsSummary>(`/analytics/summary?clinic_id=${q(clinicId)}&period=${period}`),
    daily: (clinicId: string, date: string) => request<DailyMetrics>(`/analytics/daily?clinic_id=${q(clinicId)}&date=${q(date)}`),
  },
  insurance: {
    verify: (patientId: string, memberId: string, dateOfService: string) => request<{ eligible: boolean; carrier: string; copay_primary_care: number; deductible_remaining: number }>("/insurance/verify", { method: "POST", body: JSON.stringify({ patient_id: patientId, member_id: memberId, date_of_service: dateOfService }) }),
  },
  priorAuth: {
    list: (clinicId: string, status?: string) => request<unknown[]>(`/prior-auth?clinic_id=${q(clinicId)}${status ? `&status=${q(status)}` : ""}`),
    check: (trackingNumber: string) => request<{ status: string; tracking_number: string }>(`/prior-auth/${q(trackingNumber)}/status`),
  },
  recalls: {
    list: (clinicId: string) => request<unknown[]>(`/recalls?clinic_id=${q(clinicId)}`),
    launch: (clinicId: string, recallType: string) => request<{ launched: boolean; campaign_id: string }>("/recalls/launch", { method: "POST", body: JSON.stringify({ clinic_id: clinicId, recall_type: recallType }) }),
  },
};

export { APIError };
export default api;
