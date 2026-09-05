from dataclasses import dataclass, field
from typing import Any, Protocol

INTEGRATION_STATES = frozenset({'configured','not_configured','configuration_required','healthy','degraded','unavailable','authentication_failed','rate_limited','provider_error'})

@dataclass(frozen=True)
class IntegrationError:
    code: str
    message: str
    retryable: bool = False
    provider_status: int | None = None

@dataclass(frozen=True)
class IntegrationResponse:
    data: dict[str, Any]
    provider: str
    request_id: str
    correlation_id: str | None = None
    external_reference: str | None = None

@dataclass(frozen=True)
class IntegrationHealth:
    state: str
    checked_at: str | None = None
    latency_ms: float | None = None
    error: IntegrationError | None = None

@dataclass(frozen=True)
class IntegrationCapabilities:
    fhir: bool = False
    eligibility: bool = False
    prior_authorization: bool = False
    claims: bool = False
    payments: bool = False
    messaging: bool = False
    webhooks: bool = False
    resources: tuple[str, ...] = field(default_factory=tuple)

class IntegrationProvider(Protocol):
    name: str
    version: str
    capabilities: IntegrationCapabilities
    async def health(self) -> IntegrationHealth: ...

class ProviderNotConfigured:
    name = 'unconfigured'
    version = 'none'
    capabilities = IntegrationCapabilities()
    async def health(self) -> IntegrationHealth:
        return IntegrationHealth('configuration_required', error=IntegrationError('configuration_error','Provider configuration is required.'))
