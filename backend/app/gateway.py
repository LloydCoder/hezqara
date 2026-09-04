"""
AI Gateway — Intelligent model routing with policy engine.

Each task specifies requirements; the gateway selects the best
available model that meets them. Falls back through provider chain.

Policy dimensions:
  accuracy:       low | medium | high | critical
  max_latency_ms: maximum acceptable response time
  cost_tier:      free | low | medium | high
  local_only:     PHI must not leave local machine

Model pool (preference order per policy):
  LOCAL (free, private): deepseek-coder-v2, qwen2.5:14b, qwen2.5:32b
  CLOUD FAST:            groq/llama-3.3-70b, groq/mixtral-8x7b
  CLOUD PREMIUM:         claude-sonnet-4-6
"""
import json
import logging
import time
from dataclasses import dataclass
from typing import Any, Optional

import httpx

logger = logging.getLogger(__name__)

# ── Task policies ─────────────────────────────────────────────────────────────

@dataclass
class TaskPolicy:
    task_type: str
    accuracy: str = "medium"
    max_latency_ms: int = 5000
    cost_tier: str = "free"
    local_only: bool = False
    description: str = ""


TASK_POLICIES: dict = {
    "reception_greeting":      TaskPolicy("reception_greeting",      "medium",   800,   "free"),
    "intent_detection":        TaskPolicy("intent_detection",        "high",     400,   "free"),
    "entity_extraction":       TaskPolicy("entity_extraction",       "high",     600,   "free"),
    "appointment_slot_select": TaskPolicy("appointment_slot_select", "medium",   500,   "free"),
    "appointment_reminder_text":TaskPolicy("appointment_reminder_text","medium", 1000,  "free"),
    "insurance_code_lookup":   TaskPolicy("insurance_code_lookup",   "high",     500,   "free"),
    "refill_request_parse":    TaskPolicy("refill_request_parse",    "high",     500,   "free"),
    "recall_sms_generate":     TaskPolicy("recall_sms_generate",     "medium",   1000,  "free"),
    "email_categorize":        TaskPolicy("email_categorize",        "high",     600,   "free"),
    "patient_intake_summarize":TaskPolicy("patient_intake_summarize","high",     2000,  "free"),
    "prior_auth_clinical":     TaskPolicy("prior_auth_clinical",     "critical", 15000, "high"),
    "parliament_vote":         TaskPolicy("parliament_vote",         "critical", 10000, "high"),
    "escalation_decision":     TaskPolicy("escalation_decision",     "critical", 5000,  "high"),
    "insurance_dispute":       TaskPolicy("insurance_dispute",       "critical", 15000, "high"),
    "operations_copilot":      TaskPolicy("operations_copilot",      "critical", 30000, "high"),
    "confidence_assessment":   TaskPolicy("confidence_assessment",   "high",     1000,  "low"),
}

ACCURACY_FLOOR = {"low": 4, "medium": 6, "high": 7, "critical": 9}

# ── Model pool ────────────────────────────────────────────────────────────────

@dataclass
class ModelConfig:
    model_id: str
    provider: str
    accuracy_score: int
    avg_latency_ms: int
    cost_per_1k_tokens: float
    local: bool = False
    available: bool = True


MODEL_POOL: list = [
    ModelConfig("deepseek-coder-v2",        "ollama",    6,  300,  0.0,      local=True),
    ModelConfig("qwen2.5:14b",              "ollama",    7,  600,  0.0,      local=True),
    ModelConfig("qwen2.5:32b",              "ollama",    8,  1200, 0.0,      local=True),
    ModelConfig("llama-3.3-70b-versatile",  "groq",      8,  400,  0.0006),
    ModelConfig("mixtral-8x7b-32768",       "groq",      7,  300,  0.0003),
    ModelConfig("claude-sonnet-4-6",        "anthropic", 10, 2000, 0.003),
]

# Keep backward compatibility — old imports still work
LOCAL_TASK_TYPES = {k for k, v in TASK_POLICIES.items() if v.cost_tier == "free"}
CLAUDE_TASK_TYPES = {k for k, v in TASK_POLICIES.items() if v.accuracy == "critical"}


class LLMGateway:
    """Backward-compatible alias for AIGateway."""

    def __init__(
        self,
        anthropic_api_key: str = "",
        groq_api_key: str = "",
        ollama_base_url: str = "http://localhost:11434",
    ) -> None:
        self.anthropic_api_key = anthropic_api_key
        self.groq_api_key = groq_api_key
        self.ollama_base_url = ollama_base_url
        self._metrics: list = []

    async def route(
        self,
        task_type: str,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 1000,
        **kwargs: Any,
    ) -> dict:
        policy = TASK_POLICIES.get(task_type, TaskPolicy(task_type, "medium"))
        candidates = self._select_candidates(policy)
        last_error = None

        for model in candidates:
            try:
                start = time.monotonic()
                result = await self._call_model(model, prompt, system_prompt, max_tokens)
                latency_ms = int((time.monotonic() - start) * 1000)
                self._record_metric(task_type, model.model_id, latency_ms, True, result.get("cost_usd", 0.0))
                return {
                    **result,
                    "task_type": task_type,
                    "model_used": f"{model.provider}/{model.model_id}",
                    "latency_ms": latency_ms,
                }
            except Exception as e:
                last_error = e
                logger.warning("Model %s/%s failed for %s: %s", model.provider, model.model_id, task_type, str(e))
                self._record_metric(task_type, model.model_id, 0, False, 0.0)

        logger.error("All models failed for task %s", task_type)
        return {
            "content": "",
            "task_type": task_type,
            "model_used": "none/fallback",
            "latency_ms": 0,
            "tokens_used": 0,
            "cost_usd": 0.0,
            "error": str(last_error),
            "fallback": True,
        }

    def _select_candidates(self, policy: TaskPolicy) -> list:
        floor = ACCURACY_FLOOR.get(policy.accuracy, 6)
        free_local = [
            m for m in MODEL_POOL
            if m.available and m.local and m.accuracy_score >= floor
            and m.avg_latency_ms <= policy.max_latency_ms
        ]
        cloud = [
            m for m in MODEL_POOL
            if m.available and not m.local and m.accuracy_score >= floor
        ]
        if policy.cost_tier == "free" and free_local:
            return sorted(free_local, key=lambda m: (-m.accuracy_score, m.avg_latency_ms))[:3]
        if policy.accuracy == "critical":
            return sorted(cloud, key=lambda m: -m.accuracy_score)[:3]
        all_candidates = free_local + cloud
        return sorted(all_candidates, key=lambda m: (0 if m.local else 1, -m.accuracy_score))[:3]

    async def _call_model(self, model: ModelConfig, prompt: str, system_prompt: Optional[str], max_tokens: int) -> dict:
        if model.provider == "ollama":
            return await self._call_ollama(model.model_id, prompt, system_prompt, max_tokens)
        elif model.provider == "anthropic":
            return await self._call_anthropic(model.model_id, prompt, system_prompt, max_tokens)
        elif model.provider == "groq":
            return await self._call_groq(model.model_id, prompt, system_prompt, max_tokens)
        raise ValueError(f"Unknown provider: {model.provider}")

    async def _call_ollama(self, model_id: str, prompt: str, system_prompt: Optional[str], max_tokens: int) -> dict:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                r = await client.post(
                    f"{self.ollama_base_url}/api/chat",
                    json={"model": model_id, "messages": messages, "stream": False, "options": {"num_predict": max_tokens}},
                )
                r.raise_for_status()
                data = r.json()
                return {"content": data.get("message", {}).get("content", ""), "tokens_used": data.get("eval_count", 0), "cost_usd": 0.0}
        except httpx.ConnectError:
            raise ConnectionError(f"Ollama not running at {self.ollama_base_url}")

    async def _call_anthropic(self, model_id: str, prompt: str, system_prompt: Optional[str], max_tokens: int) -> dict:
        import anthropic
        client = anthropic.AsyncAnthropic(api_key=self.anthropic_api_key)
        kwargs: dict = {"model": model_id, "max_tokens": max_tokens, "messages": [{"role": "user", "content": prompt}]}
        if system_prompt:
            kwargs["system"] = system_prompt
        response = await client.messages.create(**kwargs)
        content = response.content[0].text if response.content else ""
        in_tok, out_tok = response.usage.input_tokens, response.usage.output_tokens
        return {"content": content, "tokens_used": in_tok + out_tok, "cost_usd": round((in_tok * 0.000003) + (out_tok * 0.000015), 6)}

    async def _call_groq(self, model_id: str, prompt: str, system_prompt: Optional[str], max_tokens: int) -> dict:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        async with httpx.AsyncClient(timeout=15.0) as client:
            r = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                json={"model": model_id, "messages": messages, "max_tokens": max_tokens},
                headers={"Authorization": f"Bearer {self.groq_api_key}"},
            )
            r.raise_for_status()
            data = r.json()
            content = data["choices"][0]["message"]["content"]
            total_tokens = data.get("usage", {}).get("total_tokens", 0)
            return {"content": content, "tokens_used": total_tokens, "cost_usd": round(total_tokens * 0.0000006, 6)}

    def _record_metric(self, task_type: str, model_id: str, latency_ms: int, success: bool, cost_usd: float) -> None:
        self._metrics.append({"task_type": task_type, "model_id": model_id, "latency_ms": latency_ms, "success": success, "cost_usd": cost_usd, "timestamp": time.time()})
        if len(self._metrics) > 10_000:
            self._metrics = self._metrics[-10_000:]

    def get_metrics_summary(self) -> dict:
        if not self._metrics:
            return {}
        summary: dict = {}
        for m in self._metrics:
            tt = m["task_type"]
            if tt not in summary:
                summary[tt] = {"total": 0, "success": 0, "total_latency_ms": 0, "total_cost_usd": 0.0}
            summary[tt]["total"] += 1
            if m["success"]:
                summary[tt]["success"] += 1
            summary[tt]["total_latency_ms"] += m["latency_ms"]
            summary[tt]["total_cost_usd"] += m["cost_usd"]
        for tt, s in summary.items():
            s["success_rate"] = round(s["success"] / s["total"], 4) if s["total"] else 0
            s["avg_latency_ms"] = round(s["total_latency_ms"] / s["total"]) if s["total"] else 0
        return summary


# Alias for new code
AIGateway = LLMGateway
