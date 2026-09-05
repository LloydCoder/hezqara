# Phase 5 Integrations

Communication providers are adapter-backed. Phase 5 includes a deterministic test adapter and a WhatsApp Cloud adapter when both the business API token and phone-number ID are configured.

No provider is reported as live when configuration is missing.

Inbound provider events must be authenticated, deduplicated and validated before becoming trusted domain events. Provider identifiers are correlation data, not tenant authority.
