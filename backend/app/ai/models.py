from pydantic import BaseModel, Field
class ModelConfig(BaseModel): provider:str; model:str; temperature:float=0.0; max_tokens:int=1000
class StructuredOutput(BaseModel): data:dict; confidence:float=Field(ge=0,le=1)
