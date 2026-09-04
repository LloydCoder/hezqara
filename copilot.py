"""
Operations Copilot — AI intelligence engine for clinic owners.

This is the billion-dollar feature identified in the review.
Clinic owners ask natural language questions and get AI-powered answers.

Examples:
  "Why were appointments down last week?"
  "Which patients are most likely to miss tomorrow's appointments?"
  "How much revenue did Carenova save this month?"
  "Which receptionist tasks consume the most time?"
  "Show me every patient who missed an appointment twice."

Architecture:
  1. Parse the clinic owner's question
  2. Determine which data sources to query
  3. Fetch relevant analytics from Supabase
  4. Feed data + question to Claude Sonnet (always — this needs best model)
  5. Return structured insight with supporting data

This routes to claude-sonnet-4-6 via the AI Gateway's operations_copilot
task type (accuracy=critical, cost_tier=high).
"""
import json
import logging
from typing import Optional, Any

logger = logging.getLogger(__name__)

# Question categories and their data needs
QUESTION_CATEGORIES = {
    "appointments": ["appointment counts", "cancellations", "no-shows", "booking trends"],
    "revenue": ["revenue recovered", "cost savings", "missed appointments value"],
    "performance": ["call volume", "handle time", "agent accuracy", "fallback rate"],
    "patients": ["patient engagement", "recall response", "retention"],
    "staff": ["human handoff rate", "escalations", "tasks by type"],
    "compliance": ["audit events", "PHI access", "HIPAA score"],
}


class OperationsCopilot:
    """
    AI-powered operations intelligence for clinic owners.
    Routes through AI Gateway with operations_copilot task type.
    """

    def __init__(self, llm_gateway=None) -> None:
        self.llm = llm_gateway

    async def answer(
        self,
        question: str,
        clinic_id: str,
        context_data: Optional[dict] = None,
    ) -> dict:
        """
        Answer a natural language operations question.

        Args:
            question: Clinic owner's question in plain English
            clinic_id: Clinic to scope the analysis to
            context_data: Pre-fetched analytics data (optional)

        Returns:
            {
                "answer": "...",
                "insights": [...],
                "supporting_data": {...},
                "recommendations": [...],
                "confidence": 0.0-1.0,
            }
        """
        if not self.llm:
            return self._unavailable_response()

        # Build data context for the question
        data_summary = self._build_data_summary(context_data or {})

        system_prompt = (
            "You are the Operations Copilot for Carenova AI, an AI medical front office platform. "
            "You have access to clinic analytics data and help clinic owners understand their operations. "
            "Be specific, data-driven, and actionable. "
            "Always reference specific numbers from the data provided. "
            "Format insights as clear bullet points. "
            "If you don't have enough data to answer confidently, say so clearly."
        )

        prompt = (
            f"Clinic: {clinic_id}\n\n"
            f"Operations data:\n{data_summary}\n\n"
            f"Clinic owner's question: {question}\n\n"
            f"Please provide:\n"
            f"1. A direct answer to the question\n"
            f"2. Key insights from the data (3-5 bullet points)\n"
            f"3. Specific recommendations (2-3 actionable items)\n"
            f"4. Confidence level (0.0-1.0) in this analysis\n\n"
            f"Return as JSON:\n"
            f'{{"answer": "...", "insights": ["..."], "recommendations": ["..."], "confidence": 0.0}}'
        )

        try:
            response = await self.llm.route(
                task_type="operations_copilot",
                prompt=prompt,
                system_prompt=system_prompt,
                max_tokens=1500,
            )

            content = response.get("content", "")
            parsed = self._parse_response(content)

            return {
                **parsed,
                "supporting_data": context_data or {},
                "model_used": response.get("model_used"),
                "cost_usd": response.get("cost_usd", 0.0),
            }

        except Exception as e:
            logger.error("Operations Copilot failed for clinic %s: %s", clinic_id, str(e))
            return {
                "answer": "I was unable to analyse this data right now. Please try again.",
                "insights": [],
                "recommendations": [],
                "confidence": 0.0,
                "error": str(e),
            }

    def _build_data_summary(self, data: dict) -> str:
        """Format analytics data for LLM context."""
        if not data:
            return "No analytics data available for this time period."

        lines = []
        if "total_calls" in data:
            lines.append(f"- Total calls handled: {data['total_calls']}")
        if "total_appointments_booked" in data:
            lines.append(f"- Appointments booked: {data['total_appointments_booked']}")
        if "total_cost_savings_usd" in data:
            lines.append(f"- Cost savings: ${data['total_cost_savings_usd']:,.2f}")
        if "receptionist_hours_saved" in data:
            lines.append(f"- Receptionist hours saved: {data['receptionist_hours_saved']}")
        if "revenue_recovered_usd" in data:
            lines.append(f"- Revenue recovered: ${data['revenue_recovered_usd']:,.2f}")
        if "agent_metrics" in data:
            for agent, metrics in data["agent_metrics"].items():
                if metrics.get("total_calls"):
                    lines.append(f"- {agent.title()} agent: {metrics['total_calls']} calls, "
                                 f"{metrics.get('success_rate', 0):.0%} success rate")

        return "\n".join(lines) if lines else "Limited data available."

    def _parse_response(self, content: str) -> dict:
        """Parse structured response from LLM."""
        try:
            cleaned = content.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
            data = json.loads(cleaned)
            return {
                "answer": data.get("answer", "Analysis complete."),
                "insights": data.get("insights", []),
                "recommendations": data.get("recommendations", []),
                "confidence": float(data.get("confidence", 0.8)),
            }
        except Exception:
            return {
                "answer": content if content else "Unable to generate analysis.",
                "insights": [],
                "recommendations": [],
                "confidence": 0.5,
            }

    def _unavailable_response(self) -> dict:
        return {
            "answer": "Operations Copilot requires an AI model connection. Please configure ANTHROPIC_API_KEY.",
            "insights": [],
            "recommendations": [],
            "confidence": 0.0,
        }
