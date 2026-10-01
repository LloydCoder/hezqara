# Healthcare Interoperability Boundary

The original Phase 7 integration foundation remains the domain-level interoperability layer. E4 adds production-oriented protocol metadata and authorization controls without changing the provider-adapter abstraction.

## Standards baseline

- FHIR R4 4.0.1
- SMART App Launch 2.2.0
- Da Vinci HRex 1.2.0
- Da Vinci CRD 2.2.1
- Da Vinci DTR 2.2.0
- Da Vinci PAS 2.2.1
- Da Vinci PDex 2.2.0

## E4 controls

- Discovery requires HTTPS endpoints without embedded credentials or fragments.
- Authorization-code requests use PKCE S256 and state.
- OIDC openid requests require a nonce.
- Standalone patient context is represented through the launch/patient scope.
- EHR launch context uses the launch scope plus the launch parameter.
- Redirect URIs must be HTTPS and are never treated as arbitrary provider URLs.
- Token responses are reduced to non-secret metadata before persistence.
- OAuth sessions are expiring and one-time-use capable through used_at.
- Integration protocol capabilities are tenant scoped.
- Raw access/refresh tokens are not stored in the E4 metadata tables.

HL7 identifies SMART App Launch 2.2.0 as an OAuth 2.0-based application authorization framework and documents PKCE additions. HL7's current US Realm publication index lists the Da Vinci versions used by HEZQARA.

## Provider model

Provider adapters expose capabilities, version, environment and health. Test providers are deterministic CI-only boundaries. They must never be represented as production connectivity merely because configuration exists.

## Security

- Integration records use RLS/FORCE RLS and authenticated grants.
- Client-provided clinic IDs do not establish authority.
- Outbound HTTP retains HTTPS, trusted-host and private-destination protections.
- Webhooks require signature, timestamp and replay protection.
- External payloads remain untrusted data.

## Truthful production boundary

E4 does not claim that a specific EHR, payer, clearinghouse or messaging provider is connected. Provider-specific credentials, contracts, endpoint allowlists, sandbox certification and operational validation remain required.
