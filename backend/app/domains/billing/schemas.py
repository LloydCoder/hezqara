from decimal import Decimal
from pydantic import BaseModel, Field
class InvoiceLine(BaseModel): description:str=Field(min_length=1); amount:Decimal=Field(ge=0)
class BillingSummary(BaseModel): total:Decimal; outstanding:Decimal
