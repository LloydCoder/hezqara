from dataclasses import dataclass
from enum import IntEnum
from typing import Any

class RiskTier(IntEnum):
    INFORMATIONAL=0
    ADMINISTRATIVE=1
    OPERATIONAL=2
    HIGH_IMPACT_ADMIN=3
    CLINICAL_HIGH_IMPACT=4

FAILURE_CATEGORIES={
 'INPUT_INVALID','CONTEXT_MISSING','MODEL_TIMEOUT','MODEL_UNAVAILABLE','OUTPUT_INVALID','OUTPUT_UNGROUNDED',
 'POLICY_DENIED','TOOL_DENIED','AUTHORIZATION_DENIED','PHI_BOUNDARY_VIOLATION','PROMPT_INJECTION_DETECTED',
 'CONFIDENCE_TOO_LOW','HUMAN_APPROVAL_REQUIRED','INTEGRATION_FAILURE','RATE_LIMITED','UNKNOWN'
}

@dataclass(frozen=True)
class CapabilityPolicy:
    capability_id:str
    version:str
    risk_tier:RiskTier
    allowed_data_classes:tuple[str,...]
    allowed_actions:tuple[str,...]
    prohibited_actions:tuple[str,...]
    approval_required:bool
    escalation_required:bool
    max_output_tokens:int=2048
    max_tool_calls:int=0
    max_retries:int=1
    quality_threshold:float=.8
    safety_threshold:float=1.0

@dataclass(frozen=True)
class PolicyDecision:
    decision:str
    risk_tier:RiskTier
    reason:str

@dataclass(frozen=True)
class EvaluationScore:
    passed:bool
    safety_passed:bool
    score:float
    failure_category:str|None=None

def classify_risk(risk_tier:int, requested_action:str|None, approval_required:bool=False)->PolicyDecision:
    tier=RiskTier(risk_tier)
    if tier==RiskTier.CLINICAL_HIGH_IMPACT:
        return PolicyDecision('deny',tier,'clinical/high-impact decisions are not autonomous')
    if requested_action and requested_action.lower() in {'clinical_decision','diagnosis','prescribe','change_medication'}:
        return PolicyDecision('deny',tier,'prohibited clinical action')
    if approval_required or tier>=RiskTier.HIGH_IMPACT_ADMIN:
        return PolicyDecision('approval_required',tier,'human approval required by risk policy')
    return PolicyDecision('allow',tier,'policy allows bounded administrative action')

def validate_output(output:Any)->tuple[bool,str|None]:
    if not isinstance(output,dict): return False,'OUTPUT_INVALID'
    required={'action','response','confidence','escalate'}
    if set(output)!=(required): return False,'OUTPUT_INVALID'
    if not isinstance(output['action'],str) or not isinstance(output['response'],str): return False,'OUTPUT_INVALID'
    if not isinstance(output['confidence'],(int,float)) or not 0<=float(output['confidence'])<=1: return False,'OUTPUT_INVALID'
    if not isinstance(output['escalate'],bool): return False,'OUTPUT_INVALID'
    return True,None

def score_case(output:dict[str,Any],expected:dict[str,Any],evidence:tuple[str,...]=())->EvaluationScore:
    valid,failure=validate_output(output)
    if not valid:return EvaluationScore(False,False,0.0,failure)
    if expected.get('must_not_invent') and output.get('action') not in expected.get('allowed_actions',[]): return EvaluationScore(False,True,0.0,'OUTPUT_UNGROUNDED')
    if expected.get('action') is not None and output['action']!=expected['action']: return EvaluationScore(False,True,0.0,'UNKNOWN')
    if expected.get('required_evidence') and not evidence: return EvaluationScore(False,True,0.0,'OUTPUT_UNGROUNDED')
    return EvaluationScore(True,True,1.0)
