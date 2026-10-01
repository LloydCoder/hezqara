# E7 First-Clinic Production Vertical Slice

## Objective

Prove the end-to-end operational path for one synthetic clinic without bypassing the same authorization, tenant, workflow, governance and evidence boundaries used by production code.

## Verified flow

1. Discover and establish clinic organization context.
2. Complete onboarding and permissions.
3. Configure a deterministic FHIR test integration.
4. Verify the integration health boundary.
5. Configure subscription/entitlements.
6. Create and activate a workflow.
7. Run activation preflight.
8. Activate the clinic.
9. Execute a consequential workflow and stop at human approval.
10. Approve the action and complete the workflow.
11. Record activation evidence.
12. Produce deterministic ROI evidence.
13. Produce an operational export manifest with checksum and record counts.
14. Pause the clinic.
15. Disable the clinic.
16. Recover the clinic through a fresh preflight.
17. Roll back to the prior state.
18. Recover again and reactivate.

## Safety boundaries

- The CI clinic is synthetic.
- Deterministic test providers cannot be configured as production integrations.
- Activation requires all mandatory preflight checks.
- Workflow approval remains human-controlled.
- Export manifests contain counts/checksums rather than raw secrets.
- Activation state transitions are persisted and tenant scoped.
- A green vertical slice does not prove production provider connectivity, clinical efficacy, regulatory compliance or customer ROI.

## Evidence

- clinic_activation
- activation_evidence
- roi_snapshots
- tenant_export_manifests
- existing audit/workflow/approval/integration records

The CI workflow executes backend/tests/ci_e7_vertical_slice.py against a migrated PostgreSQL database and validates the activation tables with supabase/tests/e7_vertical_slice.sql.
