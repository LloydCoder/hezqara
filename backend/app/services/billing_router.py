"""
Billing Router — selects correct payment provider.

Routing logic:
  US Starter/Pro/Growth → LemonSqueezy (MoR, store 247127)
  US Enterprise         → Stripe (ACH + NET-30 invoicing)
  Nigeria (all tiers)   → Paystack
  Nigeria (optional)    → NOWPayments stablecoins (Phase 6)
"""


def select_payment_provider(tier: str, country: str) -> str:
    """
    Select correct payment provider based on plan tier and country.
    This is the single source of truth for payment routing.
    """
    # Nigeria: always Paystack regardless of tier
    if country == "NG":
        return "paystack"

    # US Enterprise: Stripe for ACH + NET-30
    if tier == "enterprise" and country == "US":
        return "stripe"

    # US Starter/Pro/Growth: LemonSqueezy MoR
    return "lemonsqueezy"
