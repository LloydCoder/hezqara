from .contracts import IntegrationProvider, ProviderNotConfigured

class ProviderRegistry:
    def __init__(self) -> None: self._providers: dict[str, IntegrationProvider] = {}
    def register(self, provider: IntegrationProvider) -> None:
        if not provider.name: raise ValueError('provider name is required')
        self._providers[provider.name] = provider
    def get(self, name: str) -> IntegrationProvider: return self._providers.get(name, ProviderNotConfigured())
    def list(self) -> list[IntegrationProvider]: return list(self._providers.values())

registry = ProviderRegistry()
