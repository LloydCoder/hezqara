# E4 Interoperability Verification

## Scope

E4 hardens the healthcare integration boundary around HL7 FHIR R4 4.0.1 and SMART App Launch 2.2.0.

## Verified controls

- FHIR resources enter through the explicit R4 adapter boundary.
- Supported resource types and required structural fields are validated deterministically.
- SMART discovery rejects insecure endpoints.
- Authorization-code requests use state and PKCE S256.
- OIDC authorization requests require nonce when openid is requested.
- Patient launch context is represented through the SMART scope contract.
- Raw access and refresh tokens are not returned by the metadata boundary.
- OAuth metadata is tenant scoped and RLS/FORCE RLS protected.
- E4 metadata tables do not persist raw OAuth token columns.
- Migration and tenant-integrity tests validate the protocol metadata boundary.

## Standards basis

HEZQARA documents standards versions explicitly so future upgrades can be reviewed rather than silently changing the protocol contract.

- FHIR: R4, version 4.0.1.
- SMART App Launch: version 2.2.0, based on FHIR R4.
- Da Vinci: implementation-guide versions are tracked as capabilities where implemented.

## Production boundary

Provider connectivity requires provider-specific endpoint discovery, registration, credentials, scopes, contractual authorization, sandbox/live testing and monitoring.

This repository verification does not establish provider certification, payer/EHR production connectivity, full implementation-guide conformance, HIPAA/NDPA/GDPR compliance certification or clinical interoperability efficacy.

## References

- HL7 FHIR R4 4.0.1: https://hl7.org/fhir/R4/
- HL7 SMART App Launch 2.2.0: https://hl7.org/fhir/smart-app-launch/
