export type AgentType =
  | "reception"
  | "scheduling"
  | "intake"
  | "insurance"
  | "prior_auth"
  | "refill"
  | "records"
  | "referrals"
  | "recall"
  | "email";

export type AgentStatus = "active" | "idle" | "processing" | "error" | "disabled" | "busy";

export interface Agent {
  id: AgentType;
  name: string;
  description: string;
  status: AgentStatus;
  calls_handled_today: number;
  avg_handle_time_seconds: number;
  success_rate: number;
  cost_today_usd: number;
  last_action_at: string | null;
  // Legacy API aliases kept optional while old installations migrate.
  calls_handled?: number;
  confidence_score?: number;
  avg_handle_time?: number;
}

export interface AgentEvent {
  id: string;
  agent_type: AgentType;
  clinic_id: string;
  call_id: string | null;
  event_type: string;
  payload: Record<string, unknown>;
  created_at: string;
}

export const AGENT_LABELS: Record<AgentType, string> = {
  reception: "Reception",
  scheduling: "Scheduling",
  intake: "Intake",
  insurance: "Insurance",
  prior_auth: "Prior Auth",
  refill: "Refill",
  records: "Records",
  referrals: "Referrals",
  recall: "Recall",
  email: "Email",
};

export const AGENT_DESCRIPTIONS: Record<AgentType, string> = {
  reception: "Inbound patient communication and routing",
  scheduling: "Appointment availability and booking workflows",
  intake: "Pre-visit information and insurance collection",
  insurance: "Eligibility and benefits workflow support",
  prior_auth: "Prior authorization preparation and tracking",
  refill: "Medication request intake and routing",
  records: "Medical-record request workflows",
  referrals: "Specialist referral creation and tracking",
  recall: "Proactive patient outreach campaigns",
  email: "Inbox triage and appointment communications",
};

export function agentStatusColor(status: AgentStatus): string {
  switch (status) {
    case "active":
    case "processing":
      return "#00E5CC";
    case "busy":
      return "#F5A623";
    case "idle":
      return "#94A3B8";
    case "error":
      return "#FF4D6A";
    case "disabled":
      return "#64748B";
  }
}
