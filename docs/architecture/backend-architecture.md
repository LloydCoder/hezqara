# Backend architecture

`core` contains configuration/errors/logging. `security` owns authentication, tenant context, authorization, audit and webhook verification. `api` contains transport adapters only. `domains` contain healthcare business capabilities. `workforce` contains agent identities and policies. `ai` contains model/provider/orchestration concerns. `integrations` contains vendor adapters. `infrastructure` contains database/HTTP primitives. `tasks` contains thin Celery orchestration.

Dependency rule: API → domain → repository/integration interface → infrastructure. HTTP types and vendor SDKs must not leak into domain logic.
