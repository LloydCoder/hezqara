# Incident Response Runbook

This runbook follows NIST SP 800-61r3 and the NIST CSF 2.0 lifecycle. citeturn2search16turn2search50

## 1. Prepare

Maintain owners, emergency contacts, provider escalation paths, credential-rotation procedures, backup/restore procedures and evidence storage.

## 2. Detect and analyze

Create a security incident record. Capture timestamps, tenant, affected systems, indicators, request IDs, severity and evidence. Determine whether PHI, credentials, authentication state or cross-tenant access may be involved.

## 3. Contain

- Disable affected AI capabilities or integrations.
- Revoke/rotate affected credentials.
- Revoke sessions where appropriate.
- Block compromised provider endpoints.
- Pause durable jobs/workflows if required.
- Preserve logs and audit evidence before destructive cleanup.

## 4. Eradicate

Remove malicious persistence, patch affected dependencies/configuration, invalidate compromised credentials and verify the original attack path is closed.

## 5. Recover

Restore from a known-good backup when necessary. Verify tenant isolation, authentication, integrations, AI governance and data integrity. Record measured recovery time and data-loss window.

## 6. Close and improve

Close the incident only after evidence supports recovery. Record root cause, affected scope, corrective actions, owner and due dates. Feed lessons into the threat model and CI gates.

## PHI/privacy escalation

Potential ePHI incidents require an organizational/legal assessment of applicable notification and contractual obligations. The repository does not make the legal determination.
