from dataclasses import dataclass
from typing import Protocol
from uuid import uuid4

@dataclass(frozen=True)
class EligibilityRequest:
    patient_id: str
    payer_name: str
    member_id: str
    service_code: str | None = None
    correlation_id: str | None = None

@dataclass(frozen=True)
class EligibilityResult:
    status: str
    provider: str
    provider_reference: str | None = None
    reason: str | None = None

class EligibilityProvider(Protocol):
    name: str
    async def check(self, request: EligibilityRequest) -> EligibilityResult: ...

class TestEligibilityProvider:
    name = 'test'
    async def check(self, request: EligibilityRequest) -> EligibilityResult:
        # Deterministic CI provider: no production claim is implied.
        return EligibilityResult('eligible','test',f'TEST-{uuid4().hex[:12]}')

class UnconfiguredEligibilityProvider:
    name = 'not_configured'
    async def check(self, request: EligibilityRequest) -> EligibilityResult:
        return EligibilityResult('unavailable',self.name,reason='provider_not_configured')

def build_eligibility_provider(*, app_env: str, configured: bool) -> EligibilityProvider:
    if app_env == 'test': return TestEligibilityProvider()
    return UnconfiguredEligibilityProvider() if not configured else UnconfiguredEligibilityProvider()
