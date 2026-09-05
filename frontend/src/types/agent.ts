import type { AgentType } from "@/types/agent";

export type AgentReadiness = "ready" | "unavailable" | "disabled" | "not_configured";

export interface Agent {
  id: AgentType;
  name: string;
  description?: string;
  readiness: AgentReadiness;
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
