# HEZQARA Incident Response Runbook

This runbook follows NIST SP 800-61 Rev. 3 and NIST CSF 2.0. SP 800-61 Rev. 3 is the current NIST revision and supersedes Rev. 2.

## 1. Prepare

Maintain owners, emergency contacts, provider escalation paths, credential-rotation procedures, backup/restore procedures, logging coverage and evidence storage.

Define severity and escalation criteria before an incident. Ensure responders can identify affected tenants, systems, credentials, integrations and potential PHI/ePHI scope.

## 2. Detect and analyze

Create or update the security incident record.

Capture timestamps, tenant and affected systems where known, request/correlation IDs, indicators, severity/confidence, affected credentials/sessions, possible PHI/ePHI exposure and evidence locations.

Do not copy live PHI or credentials into tickets unnecessarily.

## 3. Contain

Depending on impact:

- disable affected AI capabilities or integrations;
- revoke/rotate affected credentials;
- revoke sessions where appropriate;
- block compromised provider endpoints;
- pause durable jobs/workflows;
- isolate affected services;
- preserve logs and audit evidence before destructive cleanup.

Containment decisions should record actor, timestamp, scope and rationale.

## 4. Eradicate

Remove malicious persistence, patch affected dependencies/configuration, invalidate compromised credentials and verify that the original attack path is closed.

Re-run relevant security and tenant-isolation tests before restoring affected functionality.

## 5. Recover

Restore from a known-good backup when necessary.

Verify schema/migration compatibility, authentication/authorization, tenant isolation, AI governance, durable-job consistency, integration metadata integrity and monitoring/readiness.

Record measured RTO/RPO rather than relying on target values.

## 6. Close and improve

Close the incident only when evidence supports recovery.

Record root cause, affected scope, corrective actions, owners, due dates and verification evidence. Feed lessons into threat models, architecture decisions, tests and CI gates.

## PHI/privacy escalation

Potential ePHI incidents require an organizational/legal assessment of applicable notification, contractual and regulatory obligations. The repository does not make that legal determination.

## References

- NIST SP 800-61 Rev. 3: https://csrc.nist.gov/pubs/sp/800/61/r3/final
- NIST CSF 2.0: https://www.nist.gov/cyberframework
