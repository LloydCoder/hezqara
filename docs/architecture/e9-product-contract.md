# E9 Product & Architecture Contract

## Authority

This document is the human-readable companion to `backend/app/product/contracts.py`. The Python contract is the machine-checkable source for canonical phase and workforce ownership. Product pages and later implementation phases must not invent a second workforce taxonomy.

## Architecture chain

`identity → authorization → domain service → repository → PostgreSQL/RLS`

For governed AI execution:

`identity → authorization → capability/version → policy/risk → approval → provider/tool authorization → execution → output validation → side-effect authorization → evidence/provenance → audit/telemetry`

The client never establishes tenant authority. AI output is untrusted data. MCP is an integration interface and never becomes the authorization authority.

## Canonical enterprise phases

The contract defines exactly E9 through E24 once each. Ownership is exclusive at the phase level; later phases may depend on an earlier contract but may not silently redefine its authority.

| Phase | Owner | Contract scope |
|---|---|---|
| E9 | platform-architecture | Product, domain, workforce, workflow, tool, policy, evidence and phase ownership contracts |
| E10 | patient-access | Patient access and administrative access workflows |
| E11 | insurance-authorization | Eligibility, benefits, authorization and referral requirements |
| E12 | revenue-cycle | Claims, A/R, denials, appeals and reconciliation |
| E13 | patient-financial | Balances, statements, payments, plans, refunds and financial communications |
| E14 | document-referral | Document, fax and referral intelligence |
| E15 | ambient-documentation | Governed audio-to-draft clinical documentation |
| E16 | documentation-intelligence | Documentation extraction, quality and longitudinal intelligence |
| E17 | patient-engagement | Recall, outreach, care gaps, preferences and follow-up |
| E18 | unified-workforce | Cross-workforce orchestration |
| E19 | command-center | Operational control plane |
| E20 | ai-governance | Model/provider controls, tool gateway, MCP and safety |
| E21 | interoperability | Provider/EHR/payer productionization |
| E22 | security-compliance | Security, privacy, PHI and assurance readiness |
| E23 | reliability | Scale, resilience, backup/restore and DR |
| E24 | commercial-ga | Pilot, commercial, independent validation and GA gate |

## Canonical workforce catalog

The backend registry and public workforce surface are reconciled to the following 13 keys:

- reception — E10
- scheduling — E10
- intake — E10
- insurance — E11
- insurance_administrative — E11
- prior_authorization — E11
- revenue_cycle — E12
- records — E14
- referrals — E14
- referral_records — E14
- refill — E17
- recall — E17
- email — E17

E18 may orchestrate these workers but does not silently create a second authorization boundary.

## Interoperability baseline

HEZQARA's launch interoperability contract remains FHIR R4 4.0.1 and SMART App Launch 2.2.0. HL7 identifies FHIR R4 4.0.1 as the R4 technical-correction release, while SMART App Launch 2.2.0 is published as an R4-based implementation guide. E21 remains responsible for provider-specific conformance, profiles, credentials, endpoint validation and production evidence.

## Clinical documentation boundary

AI Scribe is draft-oriented. The system must preserve explicit clinician review, editing and approval before consequential clinical documentation is committed or written back to an external clinical system.

## Verification

`backend/tests/test_e9_product_contract.py` verifies:

1. E9–E24 are present exactly once.
2. Every canonical phase has an explicit owner and scope.
3. The canonical workforce catalog has 13 unique keys.
4. The runtime `AgentRegistry` exactly matches the canonical workforce catalog.
5. The authority and evidence chain remains explicit.

A green CI run is engineering verification of these assertions, not production, regulatory, contractual or independent-assurance proof.
