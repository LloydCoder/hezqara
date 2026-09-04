from decimal import Decimal
from app.domains.billing.service import BillingService
from app.domains.billing.schemas import InvoiceLine

def test_billing_summary():
    r=BillingService(None).summarize([InvoiceLine(description='service',amount=Decimal('10'))],Decimal('4'))
    assert r['total']==Decimal('10') and r['outstanding']==Decimal('6')
