"""Analytics schemas."""
from pydantic import BaseModel
from typing import Optional, Dict

class AnalyticsSummaryResponse(BaseModel):
    period: str
    total_calls: int = 0
    total_appointments_booked: int = 0
    total_cost_savings_usd: float = 0.0
    receptionist_hours_saved: float = 0.0
    avg_handle_time_seconds: int = 0
    patient_satisfaction_score: Optional[float] = None
    revenue_recovered_usd: float = 0.0

class AgentMetricsResponse(BaseModel):
    agent_type: str
    total_calls: int = 0
    success_rate: Optional[float] = None
    accuracy_rate: Optional[float] = None
    avg_latency_ms: Optional[int] = None
    p95_latency_ms: Optional[int] = None
    fallback_rate: Optional[float] = None
    escalation_rate: Optional[float] = None
    total_cost_usd: float = 0.0
