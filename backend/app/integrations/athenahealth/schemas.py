from pydantic import BaseModel
class AthenaPatient(BaseModel): id:str; first_name:str; last_name:str
