"""
Evaluation System — measures Carenova agent accuracy in production.

Every AI decision is tracked. Without measurement, improvement is guesswork.
Especially critical for healthcare where wrong intent = wrong outcome.

Tracks per agent, per task type:
  - Accuracy rate
  - Latency p50/p95/p99
  - Hallucination rate (flagged responses)
  - Confidence distribution
  - Cost per task
  - Fallback rate (when primary model failed)
"""
import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class EvalRecord:
    """Single evaluation event."""
    agent_type: str
    task_type: str
    clinic_id: str
    model_used: str
    success: bool
    latency_ms: int
    confidence: float
    cost_usd: float
    was_fallback: bool
    was_escalated: bool
    feedback: Optional[str] = None    # "correct" | "incorrect" | None (unknown)
    timestamp: float = field(default_factory=time.time)


class EvaluationSystem:
    """
    In-process evaluation store.
    Production: flush to Supabase eval_log table.
    """

    def __init__(self) -> None:
        self._records: list[EvalRecord] = []

    def record(
        self,
        agent_type: str,
        task_type: str,
        clinic_id: str,
        model_used: str,
        success: bool,
        latency_ms: int,
        confidence: float = 1.0,
        cost_usd: float = 0.0,
        was_fallback: bool = False,
        was_escalated: bool = False,
        feedback: Optional[str] = None,
    ) -> None:
        """Record a single AI evaluation event."""
        self._records.append(EvalRecord(
            agent_type=agent_type,
            task_type=task_type,
            clinic_id=clinic_id,
            model_used=model_used,
            success=success,
            latency_ms=latency_ms,
            confidence=confidence,
            cost_usd=cost_usd,
            was_fallback=was_fallback,
            was_escalated=was_escalated,
            feedback=feedback,
        ))
        # Keep last 50k records in memory
        if len(self._records) > 50_000:
            self._records = self._records[-50_000:]

    def get_agent_metrics(self, agent_type: str, clinic_id: Optional[str] = None) -> dict:
        """Return aggregated metrics for an agent type."""
        records = [
            r for r in self._records
            if r.agent_type == agent_type
            and (clinic_id is None or r.clinic_id == clinic_id)
        ]

        if not records:
            return self._empty_metrics(agent_type)

        latencies = sorted(r.latency_ms for r in records)
        n = len(latencies)
        labeled = [r for r in records if r.feedback in ("correct", "incorrect")]
        correct = [r for r in labeled if r.feedback == "correct"]

        return {
            "agent_type": agent_type,
            "total_calls": n,
            "success_rate": round(sum(1 for r in records if r.success) / n, 4),
            "accuracy_rate": round(len(correct) / len(labeled), 4) if labeled else None,
            "labeled_samples": len(labeled),
            "avg_latency_ms": round(sum(latencies) / n),
            "p50_latency_ms": latencies[n // 2],
            "p95_latency_ms": latencies[int(n * 0.95)],
            "p99_latency_ms": latencies[int(n * 0.99)],
            "avg_confidence": round(sum(r.confidence for r in records) / n, 4),
            "fallback_rate": round(sum(1 for r in records if r.was_fallback) / n, 4),
            "escalation_rate": round(sum(1 for r in records if r.was_escalated) / n, 4),
            "total_cost_usd": round(sum(r.cost_usd for r in records), 4),
            "avg_cost_per_call_usd": round(sum(r.cost_usd for r in records) / n, 6),
            "models_used": list({r.model_used for r in records}),
        }

    def get_platform_metrics(self) -> dict:
        """Return platform-wide metrics across all agents."""
        if not self._records:
            return {"total_calls": 0}

        n = len(self._records)
        agents = list({r.agent_type for r in self._records})

        return {
            "total_calls": n,
            "total_cost_usd": round(sum(r.cost_usd for r in self._records), 4),
            "overall_success_rate": round(sum(1 for r in self._records if r.success) / n, 4),
            "overall_fallback_rate": round(sum(1 for r in self._records if r.was_fallback) / n, 4),
            "agents_active": agents,
            "by_agent": {a: self.get_agent_metrics(a) for a in agents},
        }

    def get_task_accuracy(self, task_type: str) -> dict:
        """Accuracy breakdown for a specific task type."""
        records = [r for r in self._records if r.task_type == task_type]
        if not records:
            return {"task_type": task_type, "samples": 0}

        n = len(records)
        labeled = [r for r in records if r.feedback in ("correct", "incorrect")]

        return {
            "task_type": task_type,
            "samples": n,
            "accuracy_rate": round(len([r for r in labeled if r.feedback == "correct"]) / len(labeled), 4) if labeled else None,
            "labeled_samples": len(labeled),
            "avg_confidence": round(sum(r.confidence for r in records) / n, 4),
            "model_distribution": self._model_distribution(records),
        }

    def submit_feedback(self, agent_type: str, task_type: str, feedback: str) -> bool:
        """Submit correctness feedback for the most recent matching record."""
        matches = [
            r for r in reversed(self._records)
            if r.agent_type == agent_type and r.task_type == task_type
            and r.feedback is None
        ]
        if matches:
            matches[0].feedback = feedback
            return True
        return False

    def _empty_metrics(self, agent_type: str) -> dict:
        return {
            "agent_type": agent_type,
            "total_calls": 0,
            "success_rate": None,
            "accuracy_rate": None,
            "labeled_samples": 0,
            "avg_latency_ms": None,
            "p50_latency_ms": None,
            "p95_latency_ms": None,
            "p99_latency_ms": None,
            "avg_confidence": None,
            "fallback_rate": None,
            "escalation_rate": None,
            "total_cost_usd": 0.0,
            "avg_cost_per_call_usd": 0.0,
            "models_used": [],
        }

    def _model_distribution(self, records: list) -> dict:
        dist: dict = defaultdict(int)
        for r in records:
            dist[r.model_used] += 1
        return dict(dist)


# Global singleton — shared across all agent instances
eval_system = EvaluationSystem()
