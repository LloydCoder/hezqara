from pydantic import BaseModel
class EligibilityRequest(BaseModel): patient_id:str; payer_id:str
class EligibilityResult(BaseModel): status:str; payer_id:str; patient_id:str; source:str
