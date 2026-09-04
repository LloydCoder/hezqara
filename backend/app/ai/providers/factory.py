from app.ai.providers.anthropic import AnthropicProvider
from app.core.config import settings

def build_provider():
    if settings.anthropic_api_key:
        return AnthropicProvider()
    return None
