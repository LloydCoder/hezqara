from dataclasses import dataclass
@dataclass(frozen=True)
class PromptVersion:
    agent:str; version:str; system:str

PROMPTS={
    "reception": PromptVersion("reception","1.0","You are HEZQARA Reception. Follow authorized tools and escalate uncertain or unsafe requests."),
    "scheduling": PromptVersion("scheduling","1.0","You are HEZQARA Scheduling. Never invent availability; use authorized scheduling tools."),
}

def get_prompt(agent:str)->PromptVersion:
    return PROMPTS[agent]
