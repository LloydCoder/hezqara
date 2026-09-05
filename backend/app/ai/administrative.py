from typing import Literal
from pydantic import BaseModel, Field

class AdministrativeAIResult(BaseModel):
    classification: str
    confidence: float = Field(ge=0,le=1)
    reason: str = Field(min_length=1,max_length=1000)
    evidence_context: str = Field(default='',max_length=2000)
    recommended_action: str = Field(min_length=1,max_length=1000)
    requires_human_review: bool = True
    policy_decision: Literal['allow','review','deny'] = 'review'
    model_provider: str = 'deterministic'
    execution_id: str

def classify_denial(text: str, execution_id: str) -> AdministrativeAIResult:
    lowered=text.lower()
    if 'missing' in lowered or 'information' in lowered:
        return AdministrativeAIResult(classification='missing_information',confidence=0.95,reason='Denial text indicates missing information.',evidence_context=text[:2000],recommended_action='Review required information and prepare a corrected submission.',requires_human_review=True,execution_id=execution_id)
    if 'duplicate' in lowered:
        return AdministrativeAIResult(classification='duplicate',confidence=0.92,reason='Denial text indicates a duplicate submission.',evidence_context=text[:2000],recommended_action='Verify prior claim/submission before resubmission.',requires_human_review=True,execution_id=execution_id)
    return AdministrativeAIResult(classification='payer_review_required',confidence=0.70,reason='No deterministic administrative category matched.',evidence_context=text[:2000],recommended_action='Route to revenue-cycle human review.',requires_human_review=True,execution_id=execution_id)
