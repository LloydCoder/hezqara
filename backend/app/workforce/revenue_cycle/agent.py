from dataclasses import dataclass

@dataclass(frozen=True)
class RevenueCycleWorkforce:
    name: str = 'Revenue Cycle Workforce'
    responsibilities: tuple[str,...] = ('billing exceptions','claim preparation','denial classification','A/R prioritization','payment-state monitoring')
    required_permissions: tuple[str,...] = ('billing:read','claims:read')
