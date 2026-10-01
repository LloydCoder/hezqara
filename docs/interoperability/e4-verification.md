# E4 Interoperability Verification

## Scope

E4 hardens the healthcare integration boundary around FHIR R4 and SMART App Launch and records current Da Vinci protocol contracts.

## Verified controls

- FHIR resources are accepted only through the explicit R4 adapter boundary.
- Supported resource types and required structural fields are deterministic.
- SMART discovery rejects insecure endpoints.
- Authorization-code requests use state and PKCE S256.
- OIDC authorization requests require nonce when openid is requested.
- Patient launch context is represented through the SMART scope contract.
- Token metadata never returns raw access or refresh tokens.
- OAuth metadata tables are tenant scoped and RLS/FORCE RLS protected.
- No raw OAuth token columns exist in the E4 metadata tables.
- E4 tests validate migration state and tenant-owned protocol metadata.

## Standards evidence

HL7 identifies SMART App Launch 2.2.0 as an OAuth 2.0-based application authorization framework and documents PKCE additions. HL7's current US Realm publication index lists the Da Vinci versions used by HEZQARA.

## Non-claims

This verification does not mean:
- a provider is connected;
- a payer/EHR sandbox has certified HEZQARA;
- full implementation-guide conformance has been established;
- HIPAA/NDPA/GDPR compliance has been certified;
- clinical interoperability has been proven in production.

Those require provider-specific testing, contracts, security review and operational evidence.
