"""
Geo Pricing Service — country-based price adjustments.

US:      Full price in USD
Nigeria: ~0.30x multiplier (purchasing power parity)
UK:      Full price in GBP
SEA:     ~0.50x multiplier
"""

# USD base prices per tier
BASE_PRICES_USD = {
    "starter": 499,
    "pro": 999,
    "growth": 1999,
    "enterprise": 3999,
}

# Country multipliers (vs USD base)
COUNTRY_MULTIPLIERS = {
    "US": 1.00,
    "NG": 0.06,   # ~₦50K–₦500K when converted (NGN ~1650/USD)
    "GB": 0.90,
    "PH": 0.35,
    "IN": 0.20,
    "KE": 0.25,
    "GH": 0.20,
}

# NGN conversion (approximate)
NGN_PER_USD = 1650

# Nigeria-specific NGN prices (locked by market research)
NIGERIA_PRICES_NGN = {
    "starter": 50_000,
    "pro": 99_000,
    "growth": 199_000,
    "enterprise": 500_000,
}

COUNTRY_CURRENCIES = {
    "US": "USD",
    "NG": "NGN",
    "GB": "GBP",
    "PH": "PHP",
    "IN": "INR",
}


class GeoPricingService:
    """Returns correct price for clinic's country and plan tier."""

    def get_pricing(self, country: str, tier: str) -> dict:
        """Return pricing dict with amount, currency, and USD equivalent."""
        base_usd = BASE_PRICES_USD.get(tier, 499)
        currency = COUNTRY_CURRENCIES.get(country, "USD")

        if country == "NG":
            amount_ngn = NIGERIA_PRICES_NGN.get(tier, 50_000)
            amount_usd_equivalent = round(amount_ngn / NGN_PER_USD, 2)
            return {
                "country": country,
                "tier": tier,
                "currency": "NGN",
                "amount_ngn": amount_ngn,
                "amount_usd_equivalent": amount_usd_equivalent,
                "amount_usd": amount_usd_equivalent,
                "payment_provider": "paystack",
            }

        multiplier = COUNTRY_MULTIPLIERS.get(country, 1.0)
        amount_usd = round(base_usd * multiplier)

        return {
            "country": country,
            "tier": tier,
            "currency": currency,
            "amount_usd": amount_usd,
            "amount_usd_equivalent": amount_usd,
            "payment_provider": "stripe" if tier == "enterprise" else "lemonsqueezy",
        }
