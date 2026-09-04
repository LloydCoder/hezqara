from app.workforce.base.contracts import AgentContext, AgentRequest
from fastapi import HTTPException

PROHIBITED_TERMS=("ignore previous instructions", "reveal system prompt", "bypass authorization")

def validate_request(context:AgentContext, request:AgentRequest)->None:
    if not request.idempotency_key or len(request.idempotency_key)>200: raise HTTPException(status_code=422, detail="valid idempotency key required")
    text=str(request.input).lower()
    if any(term in text for term in PROHIBITED_TERMS): raise HTTPException(status_code=400, detail="unsafe instruction")
