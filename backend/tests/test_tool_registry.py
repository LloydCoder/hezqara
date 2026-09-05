import pytest
from app.ai.tools.registry import ToolRegistry, ToolSpec

async def _handler(**_kwargs):
    return {'ok': True}

def test_tool_registry_requires_explicit_permission():
    registry=ToolRegistry([ToolSpec('task.write','Create task','tasks:write','LOW_RISK_WRITE',_handler)])
    assert registry.authorize('task.write',frozenset({'tasks:write'})).name=='task.write'
    with pytest.raises(PermissionError): registry.authorize('task.write',frozenset({'tasks:read'}))

def test_unknown_tool_is_rejected():
    registry=ToolRegistry([])
    with pytest.raises(KeyError): registry.get('unknown')
