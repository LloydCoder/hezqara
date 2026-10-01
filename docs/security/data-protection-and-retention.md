# Data Protection, Retention & Deletion

## Data classes

| Class | Examples | Default handling |
|---|---|---|
| Identity | Clerk subject/org IDs | Minimum necessary |
| PHI | Patient, encounter, insurance and communications data | Tenant isolated; purpose-limited |
| Security evidence | Audit, incident, access review | Integrity and restricted access |
| Integration metadata | Provider IDs, protocol versions, OAuth state | No raw tokens |
| Commercial | Subscription and usage data | Tenant isolated |
| Source/telemetry | Application and operational logs | Minimize sensitive values |

## Retention

Retention is configured per deployment and contract. The E5 processing record stores the intended retention period and deletion method. Actual destructive deletion requires an approved workflow and evidence.

## Deletion

A deletion request records scope, requester, status and completion evidence. Before completion, assess legal hold, contractual retention, audit-integrity and backup implications.

## Minimization

Audit metadata is sanitized before persistence. Provider credentials and OAuth tokens are not copied into application audit metadata. External AI content is treated as untrusted and only necessary data should be supplied.

## Privacy governance

Each processor should have a documented purpose, region, data category, retention and agreement status. BAA/DPA status is evidence metadata; storing “active” is not itself proof that a signed agreement exists.
