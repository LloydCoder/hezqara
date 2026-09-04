from pydantic import BaseModel
class PriorAuthorizationRequest(BaseModel): patient_id:str; payer_id:str; procedure_code:str
class PriorAuthorizationResult(BaseModel): status:str; reference_id:str|None=None
