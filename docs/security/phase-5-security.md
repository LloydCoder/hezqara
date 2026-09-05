# Phase 5 Security

HEZQARA Phase 5 applies defense in depth for tenant isolation and agentic operations.

- Clerk organization context is authoritative for tenant identity.
- Server-side permissions protect each operational action.
- PostgreSQL RLS is enabled and forced on Phase 5 tenant tables.
- `anon` has no Phase 5 table grants.
- AI input is treated as untrusted content.
- Structured AI outputs are validated before use.
- Agents do not receive arbitrary SQL, shell or unrestricted network access.
- External communication uses an outbox and idempotency key.
- Provider webhooks must be authenticated before they can become trusted application events.
- Appointment writes are protected by transactional overlap guards.
- Logs and telemetry must not contain unnecessary patient data or secrets.

The design follows current OWASP API and GenAI/agentic guidance and HIPAA Security Rule considerations. It does not constitute a legal HIPAA compliance certification.
