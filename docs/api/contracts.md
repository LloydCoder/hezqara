# API contracts

Versioned application endpoints live under `/api/v1`. Webhooks live under `/webhooks/*` and are independently authenticated by provider signature. Sensitive endpoints enforce both authentication and application permissions. Resource access is tenant-scoped on the server.
