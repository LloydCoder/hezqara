// Analytics and clinic types

export type PlanTier = "starter" | "pro" | "growth" | "enterprise";

export interface Clinic {
  id: string;
  name: string;
  clerk_org_id: string;
  ehr_type: string;
  phone_number: string | null;
  timezone: string;
  country: "US" | "NG" | "GB" | string;
  plan_tier: PlanTier;
  active_agents: string[];
  hipaa_baa_signed: boolean;
  created_at: string;
}

export interface DailyMetrics {
  date: string;
  calls_handled: number;
  appointments_booked: number;
  refills_processed: number;
  recalls_sent: number;
  prior_auths_submitted: number;
  records_released: number;
  referrals_created: number;
  cost_savings_usd: number;
  ai_cost_usd: number;
  calls_per_agent: Record<string, number>;
}

export interface AnalyticsSummary {
  period: "today" | "week" | "month";
  total_calls: number;
  total_appointments_booked: number;
  total_cost_savings_usd: number;
  receptionist_hours_saved: number;
  avg_handle_time_seconds: number;
  patient_satisfaction_score: number | null;
  revenue_recovered_usd: number;
}

export interface PlanFeatures {
  starter: string[];
  pro: string[];
  growth: string[];
  enterprise: string[];
}

export const PLAN_PRICES: Record<PlanTier, number> = {
  starter: 499,
  pro: 999,
  growth: 1999,
  enterprise: 3999,
};

export const PLAN_PROVIDER_LIMITS: Record<PlanTier, string> = {
  starter: "1–2 providers",
  pro: "3–5 providers",
  growth: "6–15 providers",
  enterprise: "15+ providers",
};
