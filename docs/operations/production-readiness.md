# Production readiness

Required environment configuration is supplied by deployment infrastructure. Health endpoints must not expose secrets. Data migrations are versioned. Workers use explicit queues, bounded task timeouts and retries. Production deployments must use TLS, secret management, backups and monitoring appropriate to the deployment.
