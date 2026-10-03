# E21 — Interoperability & Provider Productionization

Status: IMPLEMENTED — awaiting CI/evidence gate.

E21 makes provider integrations explicit, tenant-scoped and health-verifiable. Connection records distinguish FHIR/SMART/payer/payment/messaging/document interfaces, sandbox vs production, supported resources and verification state.

Connection registration never stores provider secrets. Actual credentials remain in the deployment secret manager. Verification records operational health, not certification.
