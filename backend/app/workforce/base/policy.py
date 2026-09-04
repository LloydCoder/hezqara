from app.workforce.base.contracts import AgentContext,AgentRequest
class PermissionPolicy:
    def __init__(self,permission:str): self.permission=permission
    def validate(self,context:AgentContext,request:AgentRequest)->None:
        if self.permission not in context.permissions: raise PermissionError("agent permission denied")
