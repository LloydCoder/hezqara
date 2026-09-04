// Agent types — all 9 agents + email

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

export type AgentStatus = "active" | "idle" | "processing" | "error" | "disabled";

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
  reception: "Answers every inbound call, greets patients, detects intent",
  scheduling: "Books, reschedules, and cancels appointments in EHR",
  intake: "Collects demographics, insurance, and medical history",
  insurance: "Verifies eligibility and benefits in real time",
  prior_auth: "Submits and tracks prior authorization requests",
  refill: "Processes medication refill requests to pharmacy",
  records: "Releases medical records with identity verification",
  referrals: "Creates and tracks specialist referrals",
  recall: "Sends proactive recall campaigns to fill the schedule",
  email: "Triages inbox, drafts replies, sends confirmations",
};
