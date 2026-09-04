import json
from anthropic import AsyncAnthropic
from app.core.config import settings
class AnthropicProvider:
    def __init__(self):
        if not settings.anthropic_api_key:raise RuntimeError("ANTHROPIC_API_KEY is not configured")
        self.client=AsyncAnthropic(api_key=settings.anthropic_api_key)
    async def generate(self,*,system_prompt,user_input,model=None,temperature=0.0,max_tokens=1200)->str:
        response=await self.client.messages.create(model=model or settings.ai_model,system=system_prompt,messages=[{"role":"user","content":user_input}],temperature=temperature,max_tokens=max_tokens)
        text="".join(block.text for block in response.content if getattr(block,"type",None)=="text")
        if not text:raise RuntimeError("model returned no text content")
        return text
    async def structured_output(self,*,system_prompt,user_input,model=None,schema,**kwargs):
        raw=await self.generate(system_prompt=f"{system_prompt}\nReturn only valid JSON matching this schema: {json.dumps(schema,separators=(',',':'))}",user_input=user_input,model=model,**kwargs)
        try:return json.loads(raw)
        except json.JSONDecodeError as exc:raise ValueError("model returned invalid JSON") from exc
