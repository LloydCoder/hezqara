# E21 Architecture

Provider connection registry → credential/secret manager → FHIR/SMART/payer/payment/messaging/document adapter → domain workflow.

The registry stores non-secret integration metadata and health evidence. It does not become a credential store or replace domain-specific adapters.
