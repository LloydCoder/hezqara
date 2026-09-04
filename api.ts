// Typed API client — all Carenova backend endpoints
// Backend: FastAPI on EC2 Stockholm port 8004

import type { Agent, AgentType } from "@/types/agent";
import type { Patient, Appointment, Call } from "@/types/patient";
import type { DailyMetrics, AnalyticsSummary } from "@/types/analytics";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8004";

class APIError extends Error {
  constructor(
    message: string,
    public status: number,
    public data?: unknown
  ) {
    super(message);
    this.name = "APIError";
  }
}

async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${BASE_URL}${path}`;
  const res = await fetch(url, {
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
    ...options,
  });

  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new APIError(
      data.detail ?? `API error ${res.status}`,
      res.status,
      data
    );
  }

  return res.json() as Promise<T>;
}

// ── Health ────────────────────────────────────────────────────────────────────

export const api = {
  health: {
    check: () =>
      request<{ status: string; service: string; port: number }>("/health"),
  },

  // ── Agents ──────────────────────────────────────────────────────────────────

  agents: {
    list: (clinicId: string) =>
      request<Agent[]>(`/agents?clinic_id=${clinicId}`),

    get: (clinicId: string, agentType: AgentType) =>
      request<Agent>(`/agents/${agentType}?clinic_id=${clinicId}`),

    toggle: (clinicId: string, agentType: AgentType, enabled: boolean) =>
      request<{ updated: boolean }>(`/agents/${agentType}/toggle`, {
        method: "POST",
        body: JSON.stringify({ clinic_id: clinicId, enabled }),
      }),
  },

  // ── Calls ───────────────────────────────────────────────────────────────────

  calls: {
    list: (clinicId: string, limit = 50) =>
      request<Call[]>(`/calls?clinic_id=${clinicId}&limit=${limit}`),

    get: (callId: string) =>
      request<Call & { transcript: unknown[] }>(`/calls/${callId}`),
  },

  // ── Appointments ─────────────────────────────────────────────────────────────

  appointments: {
    list: (clinicId: string, status?: string) =>
      request<Appointment[]>(
        `/appointments?clinic_id=${clinicId}${status ? `&status=${status}` : ""}`
      ),

    get: (appointmentId: string) =>
      request<Appointment>(`/appointments/${appointmentId}`),

    cancel: (appointmentId: string, reason: string) =>
      request<{ success: boolean }>(`/appointments/${appointmentId}/cancel`, {
        method: "POST",
        body: JSON.stringify({ reason }),
      }),
  },

  // ── Patients ─────────────────────────────────────────────────────────────────

  patients: {
    list: (clinicId: string, search?: string) =>
      request<Patient[]>(
        `/patients?clinic_id=${clinicId}${search ? `&search=${search}` : ""}`
      ),

    get: (patientId: string) =>
      request<Patient>(`/patients/${patientId}`),
  },

  // ── Analytics ────────────────────────────────────────────────────────────────

  analytics: {
    summary: (clinicId: string, period: "today" | "week" | "month") =>
      request<AnalyticsSummary>(
        `/analytics/summary?clinic_id=${clinicId}&period=${period}`
      ),

    daily: (clinicId: string, date: string) =>
      request<DailyMetrics>(
        `/analytics/daily?clinic_id=${clinicId}&date=${date}`
      ),
  },

  // ── Insurance ────────────────────────────────────────────────────────────────

  insurance: {
    verify: (patientId: string, memberId: string, dateOfService: string) =>
      request<{
        eligible: boolean;
        carrier: string;
        copay_primary_care: number;
        deductible_remaining: number;
      }>("/insurance/verify", {
        method: "POST",
        body: JSON.stringify({
          patient_id: patientId,
          member_id: memberId,
          date_of_service: dateOfService,
        }),
      }),
  },

  // ── Prior Auth ───────────────────────────────────────────────────────────────

  priorAuth: {
    list: (clinicId: string, status?: string) =>
      request<unknown[]>(
        `/prior-auth?clinic_id=${clinicId}${status ? `&status=${status}` : ""}`
      ),

    check: (trackingNumber: string) =>
      request<{ status: string; tracking_number: string }>(
        `/prior-auth/${trackingNumber}/status`
      ),
  },

  // ── Recalls ──────────────────────────────────────────────────────────────────

  recalls: {
    list: (clinicId: string) =>
      request<unknown[]>(`/recalls?clinic_id=${clinicId}`),

    launch: (clinicId: string, recallType: string) =>
      request<{ launched: boolean; campaign_id: string }>("/recalls/launch", {
        method: "POST",
        body: JSON.stringify({ clinic_id: clinicId, recall_type: recallType }),
      }),
  },
};

export { APIError };
export default api;
