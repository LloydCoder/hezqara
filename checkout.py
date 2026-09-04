"""
Checkout URL Service — LemonSqueezy, Stripe, Paystack.
Generates correct checkout URLs per tier, country, and payment provider.

LemonSqueezy store: 247127
Product IDs must be created in LemonSqueezy dashboard first.
"""
import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# ── LemonSqueezy product variant IDs (set in .env after creating products) ──
# Create these at app.lemonsqueezy.com → Store 247127 → Products
LEMON_VARIANTS = {
    "starter": os.getenv("LEMON_VARIANT_STARTER", ""),
    "pro":     os.getenv("LEMON_VARIANT_PRO",     ""),
    "growth":  os.getenv("LEMON_VARIANT_GROWTH",  ""),
}
LEMON_BASE = "https://carenova.lemonsqueezy.com/checkout/buy"

# ── Stripe payment links (set in .env after creating in Stripe dashboard) ──
STRIPE_LINKS = {
    "enterprise": os.getenv("STRIPE_LINK_ENTERPRISE", ""),
}

# ── Paystack plans (set in .env after creating in Paystack dashboard) ──
PAYSTACK_PLANS = {
    "starter": os.getenv("PAYSTACK_PLAN_STARTER_NG", ""),
    "pro":     os.getenv("PAYSTACK_PLAN_PRO_NG",     ""),
    "growth":  os.getenv("PAYSTACK_PLAN_GROWTH_NG",  ""),
}
PAYSTACK_BASE = "https://paystack.com/pay"


def get_checkout_url(
    tier: str,
    country: str = "US",
    clinic_id: Optional[str] = None,
    email: Optional[str] = None,
) -> dict:
    """
    Get checkout URL for a given tier and country.
    Returns URL + payment provider + currency + amount.
    """
    tier = tier.lower()
    country = country.upper()

    # Nigeria → Paystack
    if country == "NG":
        plan_id = PAYSTACK_PLANS.get(tier, "")
        if plan_id:
            url = f"{PAYSTACK_BASE}/{plan_id}"
        else:
            url = f"https://carenova.tinlance.com/pricing?tier={tier}&country=NG"
        prices = {"starter": 25_000, "pro": 49_000, "growth": 99_000, "enterprise": 199_000}
        return {
            "url": url,
            "provider": "paystack",
            "currency": "NGN",
            "amount": prices.get(tier, 25_000),
            "formatted": f"₦{prices.get(tier, 25_000):,}/month",
        }

    # Enterprise → Stripe
    if tier == "enterprise":
        url = STRIPE_LINKS.get("enterprise") or "mailto:lloyd@tinlance.com?subject=Enterprise Plan"
        return {
            "url": url,
            "provider": "stripe",
            "currency": "USD",
            "amount": 3999,
            "formatted": "$3,999/month",
            "note": "ACH transfer + NET-30 invoicing available",
        }

    # US Starter/Pro/Growth → LemonSqueezy
    variant_id = LEMON_VARIANTS.get(tier, "")
    params = []
    if clinic_id:
        params.append(f"checkout[custom][clinic_id]={clinic_id}")
    if email:
        params.append(f"checkout[email]={email}")

    if variant_id:
        url = f"{LEMON_BASE}/{variant_id}"
        if params:
            url += "?" + "&".join(params)
    else:
        url = f"https://carenova.tinlance.com/pricing?tier={tier}"

    prices = {"starter": 499, "pro": 999, "growth": 1999}
    return {
        "url": url,
        "provider": "lemonsqueezy",
        "currency": "USD",
        "amount": prices.get(tier, 499),
        "formatted": f"${prices.get(tier, 499)}/month",
    }


def get_all_checkout_urls(country: str = "US") -> dict:
    """Returns checkout URLs for all tiers for a given country."""
    tiers = ["starter", "pro", "growth", "enterprise"]
    return {tier: get_checkout_url(tier, country) for tier in tiers}
