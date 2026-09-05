# Phase 5 AI Governance

AI is an untrusted reasoning component, not an authorization boundary.

## Controls

1. Minimize inputs to the task-required fields.
2. Treat patient messages and external content as data, never instructions.
3. Require structured model output and schema validation.
4. Apply deterministic policy checks after model output.
5. Keep tenant identity outside model control.
6. Bind consequential tool calls to server-side permissions.
7. Require human approval for configured high-risk or external side effects.
8. Bound workflow steps, retries, execution duration and payload sizes.
9. Persist execution and approval lineage.
10. Escalate clinical content rather than making autonomous clinical decisions.

Phase 5 follows NIST AI RMF/Generative AI Profile concepts and the current OWASP GenAI and Agentic AI guidance, including the 2026 agentic security material.
