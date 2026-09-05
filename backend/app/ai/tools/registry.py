from dataclasses import dataclass
from typing import Any, Awaitable, Callable

@dataclass(frozen=True)
class ToolSpec:
    name:str
    description:str
    required_permission:str
    risk_level:str
    handler:Callable[...,Awaitable[dict[str,Any]]]

class ToolRegistry:
    def __init__(self,tools:list[ToolSpec]): self._tools={tool.name:tool for tool in tools}
    def get(self,name:str)->ToolSpec:
        if name not in self._tools: raise KeyError('unknown tool')
        return self._tools[name]
    def authorize(self,name:str,permissions:frozenset[str])->ToolSpec:
        tool=self.get(name)
        if tool.required_permission not in permissions: raise PermissionError('tool permission denied')
        return tool
    def names(self)->list[str]: return sorted(self._tools)
