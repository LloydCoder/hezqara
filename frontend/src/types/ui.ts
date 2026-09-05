export type ReadinessState = "ready" | "unavailable" | "disabled" | "not_configured";
export type ExecutionState = "queued" | "running" | "waiting_for_approval" | "completed" | "failed" | "escalated" | "cancelled";
export type StatusTone = "success" | "warning" | "danger" | "info" | "neutral" | "pending";

export const READINESS_LABELS: Record<ReadinessState, string> = {
  ready: "Ready",
  unavailable: "Unavailable",
  disabled: "Disabled",
  not_configured: "Not configured",
};

export const EXECUTION_LABELS: Record<ExecutionState, string> = {
  queued: "Queued",
  running: "Running",
  waiting_for_approval: "Waiting for approval",
  completed: "Completed",
  failed: "Failed",
  escalated: "Escalated",
  cancelled: "Cancelled",
};

export function readinessTone(state: ReadinessState): StatusTone {
  return state === "ready" ? "success" : state === "unavailable" ? "neutral" : state === "not_configured" ? "warning" : "neutral";
}

export function executionTone(state: ExecutionState): StatusTone {
  if (state === "completed") return "success";
  if (state === "failed" || state === "escalated") return "danger";
  if (state === "waiting_for_approval") return "warning";
  if (state === "running") return "info";
  if (state === "queued") return "pending";
  return "neutral";
}
