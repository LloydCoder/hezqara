# Phase 7 — Healthcare Interoperability

Phase 7 establishes a governed external-integration boundary on the Phase 6 administrative domain engine.

## Canonical flow

`Authenticated UI → tenant/policy → domain service → integration port → provider adapter → validated external result → domain state → audit/observability`

AI never selects arbitrary endpoints, credentials, OAuth scopes or providers. Third-party content is explicitly treated as untrusted data before any AI processing.

## Standards baseline

The implementation targets an explicit FHIR R4 boundary. SMART App Launch 2.2.0 is the OAuth-based foundation for FHIR application authorization. Da Vinci HRex 1.2.0 is a cross-guide foundation; current published Da Vinci artifacts include PDex 2.2.0, DTR 2.2.0 and PAS 2.2.1. These standards inform adapter contracts; this repository does not claim certification or full implementation-guide conformance.

CMS interoperability/prior-authorization requirements are treated as external regulatory context, not as a certification claim.

## Provider model

Provider adapters expose capabilities, version, environment and health. Test providers (`test-fhir`, `test-ehr`, `test-eligibility`, `test-authorization`, `test-clearinghouse`, `test-payment`, `test-messaging`) are deterministic CI-only boundaries. They must never be configured as production providers.

Production provider connectivity remains configuration-dependent until real credentials, endpoint allowlists, contracts and sandbox/production validation are supplied.

## Security

- Integration records are tenant-owned with PostgreSQL RLS/FORCE RLS and authenticated grants.
- Credentials are represented only by opaque metadata references; raw secrets are not persisted by this layer.
- Outbound HTTP requires HTTPS and an explicit host allowlist and rejects non-public DNS targets, embedded credentials and redirects.
- Webhooks require authenticated signatures, timestamps and event-id replay protection.
- External payloads are untrusted data and cannot become authorization or tool instructions.

## Reliability

Normalized errors distinguish validation, authentication, authorization, rate limiting, timeout, network, provider rejection, provider availability and malformed responses. Retry classification is bounded and excludes permanent failures.

Database state includes integration requests, external references, webhook events, synchronization runs, failure records, health observations and provider rate-limit state. These records are intended to support outbox/inbox processing, reconciliation and operational recovery as concrete provider adapters are added.

## Truthful states

`not_configured`, `configuration_required`, `healthy`, `degraded`, `unavailable`, `authentication_failed`, `rate_limited` and `provider_error` are distinct. A credential existing in configuration is not evidence that a provider is connected or healthy.

## References

- HL7 FHIR R4 and SMART App Launch 2.2.0
- HL7 US Core
- HL7 Da Vinci HRex, PDex, CRD, DTR and PAS
- CMS-0057-F
- OWASP API Security Top 10 2023
- NIST AI RMF

No HIPAA/GDPR/FHIR/SMART/CMS/SOC 2/ISO certification or compliance claim is made by this engineering documentation.
