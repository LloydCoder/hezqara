from anthropic import AsyncAnthropic
from app.core.config import settings
class AnthropicProvider:
    def __init__(self): self.client=AsyncAnthropic(api_key=settings.anthropic_api_key)
    async def generate(self, *, system_prompt, user_input, model, temperature=0.0, max_tokens=1000):
        r=await self.client.messages.create(model=model,system=system_prompt,messages=[{"role":"user","content":user_input}],temperature=temperature,max_tokens=max_tokens)
        return r.content[0].text
    async def structured_output(self, **kwargs):
        raise NotImplementedError("Use a schema-capable wrapper for provider-specific structured output")
