from decimal import Decimal
from app.domains.billing.schemas import InvoiceLine
from app.domains.billing.service import BillingService

def test_billing_summary():
    result=BillingService().summarize([InvoiceLine(description='service',amount=Decimal('10'))],Decimal('4'))
    assert result['total']==Decimal('10') and result['outstanding']==Decimal('6')
