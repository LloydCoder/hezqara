from decimal import Decimal
from app.domains.billing.schemas import InvoiceLine
class BillingService:
    """Clinic/patient financial workflow; separate from HEZQARA subscription billing."""
    def summarize(self, lines:list[InvoiceLine], paid:Decimal=Decimal("0")) -> dict:
        total=sum((line.amount for line in lines),Decimal("0")); return {"total":total,"outstanding":max(total-paid,Decimal("0"))}
