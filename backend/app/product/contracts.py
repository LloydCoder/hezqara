from __future__ import annotations

from typing import Final, TypedDict


class PhaseContract(TypedDict):
    key: str
    name: str
    owner: str
    scope: str


class WorkforceContract(TypedDict):
    key: str
    name: str
    owner_phase: str
    role: str


CANONICAL_PHASES: Final[tuple[PhaseContract, ...]] = (
    {"key": "E9", "name": "Product & Architecture Finalization", "owner": "platform-architecture", "scope": "canonical product, domain, workforce, workflow, tool, policy, evidence and phase-ownership contracts"},
    {"key": "E10", "name": "Patient Access Workforce", "owner": "patient-access", "scope": "access, intake, registration, scheduling and administrative patient-access workflows"},
    {"key": "E11", "name": "Insurance & Authorization Workforce", "owner": "insurance-authorization", "scope": "eligibility, benefits, authorization and referral requirements"},
    {"key": "E12", "name": "Revenue Cycle Workforce", "owner": "revenue-cycle", "scope": "claims, accounts receivable, denials, appeals and reconciliation"},
    {"key": "E13", "name": "Patient Financial Workforce", "owner": "patient-financial", "scope": "balances, statements, payments, plans, refunds and financial communications"},
    {"key": "E14", "name": "Document, Fax & Referral Intelligence", "owner": "document-referral", "scope": "ingestion, classification, extraction, routing and evidence-backed document/referral workflows"},
    {"key": "E15", "name": "Ambient Clinical Documentation / AI Scribe", "owner": "ambient-documentation", "scope": "audio-to-draft clinical documentation with explicit clinician review and approval"},
    {"key": "E16", "name": "Documentation Intelligence", "owner": "documentation-intelligence", "scope": "structured documentation extraction, quality and longitudinal intelligence"},
    {"key": "E17", "name": "Patient Engagement & Care-Gap Workforce", "owner": "patient-engagement", "scope": "recall, outreach, care gaps, preferences, consent and follow-up"},
    {"key": "E18", "name": "Unified Healthcare AI Workforce", "owner": "unified-workforce", "scope": "cross-workforce orchestration without duplicating authorization or audit authority"},
    {"key": "E19", "name": "HEZQARA Command Center", "owner": "command-center", "scope": "operational control plane for workforce, workflow, evidence, integrations and exceptions"},
    {"key": "E20", "name": "AI Governance, MCP & Clinical Documentation Safety", "owner": "ai-governance", "scope": "model/provider controls, tool gateway, MCP interface, adversarial safety and documentation integrity"},
    {"key": "E21", "name": "Interoperability & Provider Productionization", "owner": "interoperability", "scope": "real provider, EHR and payer integration contracts, conformance and production evidence"},
    {"key": "E22", "name": "Enterprise Security & Compliance Readiness", "owner": "security-compliance", "scope": "security, privacy, PHI, contractual and independent-assurance readiness"},
    {"key": "E23", "name": "Reliability, Scale & Disaster Recovery", "owner": "reliability", "scope": "capacity, resilience, backup/restore, DR, failover and operational scale evidence"},
    {"key": "E24", "name": "Commercialization, Independent Validation & General Availability", "owner": "commercial-ga", "scope": "pilot evidence, unit economics, contracts, external validation and GA gate"},
)

CANONICAL_WORKFORCES: Final[tuple[WorkforceContract, ...]] = (
    {"key": "reception", "name": "Reception Agent", "owner_phase": "E10", "role": "front-office request handling and routing"},
    {"key": "scheduling", "name": "Scheduling Agent", "owner_phase": "E10", "role": "scheduling, rescheduling, cancellation and availability coordination"},
    {"key": "intake", "name": "Intake Agent", "owner_phase": "E10", "role": "administrative intake and registration coordination"},
    {"key": "insurance", "name": "Insurance Agent", "owner_phase": "E11", "role": "insurance verification and administrative follow-up"},
    {"key": "insurance_administrative", "name": "Insurance Administrative Agent", "owner_phase": "E11", "role": "payer administration and coverage workflow support"},
    {"key": "prior_authorization", "name": "Prior Authorization Agent", "owner_phase": "E11", "role": "authorization preparation, status and follow-up"},
    {"key": "revenue_cycle", "name": "Revenue Cycle Agent", "owner_phase": "E12", "role": "claims and revenue-cycle operations"},
    {"key": "records", "name": "Records Agent", "owner_phase": "E14", "role": "records-request coordination and status management"},
    {"key": "referrals", "name": "Referrals Agent", "owner_phase": "E14", "role": "referral intake, routing and follow-up"},
    {"key": "referral_records", "name": "Referral Records Agent", "owner_phase": "E14", "role": "referral documentation and record coordination"},
    {"key": "refill", "name": "Refill Agent", "owner_phase": "E17", "role": "administrative refill routing with escalation boundaries"},
    {"key": "recall", "name": "Recall Agent", "owner_phase": "E17", "role": "recall and governed follow-up outreach"},
    {"key": "email", "name": "Email Agent", "owner_phase": "E17", "role": "operational email drafting and coordination"},
)

ARCHITECTURE_LAYERS: Final[tuple[str, ...]] = (
    "identity",
    "authorization",
    "domain_service",
    "repository",
    "postgresql_rls",
    "ai_governance",
    "policy",
    "approval",
    "execution",
    "output_validation",
    "evidence_provenance",
    "audit_telemetry",
)

_PHASE_KEYS = {phase["key"] for phase in CANONICAL_PHASES}
if len(_PHASE_KEYS) != len(CANONICAL_PHASES):
    raise RuntimeError("duplicate canonical phase key")
if len({item["key"] for item in CANONICAL_WORKFORCES}) != len(CANONICAL_WORKFORCES):
    raise RuntimeError("duplicate canonical workforce key")
if any(item["owner_phase"] not in _PHASE_KEYS for item in CANONICAL_WORKFORCES):
    raise RuntimeError("workforce references unknown owning phase")
