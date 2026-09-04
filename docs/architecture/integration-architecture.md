# Integration architecture

External systems are isolated under `backend/app/integrations`. Domain code calls stable interfaces. Adapters own authentication, request/response mapping, provider-specific errors, timeouts and retries. Webhook receivers are separate from authenticated API routes and verify provider signatures before processing events.
