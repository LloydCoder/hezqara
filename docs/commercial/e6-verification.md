# E6 Commercial Platform Verification

## Verified engineering boundary

- Canonical clinic identity is resolved server-side from the authenticated organization.
- Subscription state is persisted in PostgreSQL.
- Plan catalog and entitlements are persisted and tenant scoped.
- Stripe Checkout is created server-side using configured provider price IDs.
- Checkout creation accepts an idempotency key.
- Stripe webhook signatures are verified by the Stripe SDK.
- Provider event IDs are durably deduplicated in PostgreSQL.
- Subscription state transitions are driven by verified provider events rather than client claims.
- Invoice payment/failure/finalization/void events are represented in a commercial ledger.
- Provider customer/subscription/price identifiers are persisted as references.
- Tenant-scoped commercial tables use RLS/FORCE RLS.
- Manual plan changes remain available as an administrative/testing path and are not treated as proof of payment.

Stripe's API supports idempotency keys for safe retries, and Checkout Sessions support recurring subscription mode, client references and metadata used for reconciliation. Stripe publishes subscription and invoice webhook event types that are used by the state machine.

## Non-claims

E6 does not claim a live Stripe account is configured, that a payment has been processed in production, or that tax, refunds, disputes, chargebacks and accounting reconciliation have been operationally proven. Those require provider configuration, sandbox/live testing and financial controls.
