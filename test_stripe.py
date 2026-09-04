"""
Stripe Service Tests — Sprint 15 Addition
TDD RED phase.

Stripe handles Enterprise tier ($3,999/month) specifically:
  - ACH bank transfers (avoids 2.9% card fee on large amounts)
  - NET-30 invoicing for hospital systems
  - Custom enterprise contracts
  - HSA/FSA payment acceptance
  - Webhook handling for payment events

LemonSqueezy handles Starter/Pro/Growth.
Stripe handles Enterprise only.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient


class TestStripeServiceInitialisation:

    def test_stripe_service_can_be_imported(self):
        from app.services.stripe_service import StripeService
        assert StripeService is not None

    def test_stripe_service_requires_api_key(self):
        from app.services.stripe_service import StripeService
        with pytest.raises(TypeError):
            StripeService()

    def test_stripe_service_stores_api_key(self):
        from app.services.stripe_service import StripeService
        svc = StripeService(api_key="sk_test_abc123")
        assert svc.api_key == "sk_test_abc123"

    def test_stripe_service_is_enterprise_only(self):
        """Stripe is only for Enterprise tier — enforced at service level."""
        from app.services.stripe_service import StripeService
        svc = StripeService(api_key="sk_test_abc123")
        assert svc.tier == "enterprise"


class TestStripeSubscriptionManagement:

    @pytest.mark.asyncio
    async def test_create_enterprise_subscription_returns_id(self):
        """Creates Stripe subscription for Enterprise clinic."""
        from app.services.stripe_service import StripeService

        svc = StripeService(api_key="sk_test_abc123")

        with patch.object(svc, "_create_subscription", return_value={
            "id": "sub_stripe_001",
            "status": "active",
            "current_period_end": 1751328000,
            "plan": "enterprise",
        }):
            result = await svc.create_enterprise_subscription(
                clinic_id="clinic_test_001",
                customer_email="billing@familycare.com",
                payment_method="pm_card_visa",
            )

        assert result["success"] is True
        assert result["subscription_id"] == "sub_stripe_001"
        assert result["plan_tier"] == "enterprise"

    @pytest.mark.asyncio
    async def test_get_subscription_status_returns_active(self):
        """Returns active status for valid Stripe subscription."""
        from app.services.stripe_service import StripeService

        svc = StripeService(api_key="sk_test_abc123")

        with patch.object(svc, "_get_subscription", return_value={
            "status": "active",
            "plan": {"nickname": "Enterprise"},
            "current_period_end": 1751328000,
        }):
            result = await svc.get_subscription_status(
                subscription_id="sub_stripe_001"
            )

        assert result["active"] is True
        assert result["plan_tier"] == "enterprise"

    @pytest.mark.asyncio
    async def test_cancelled_subscription_returns_inactive(self):
        """Cancelled Stripe subscription returns active=False."""
        from app.services.stripe_service import StripeService

        svc = StripeService(api_key="sk_test_abc123")

        with patch.object(svc, "_get_subscription", return_value={
            "status": "canceled",
            "plan": {"nickname": "Enterprise"},
        }):
            result = await svc.get_subscription_status(
                subscription_id="sub_stripe_001"
            )

        assert result["active"] is False


class TestStripeACHPayments:

    @pytest.mark.asyncio
    async def test_create_ach_payment_intent(self):
        """ACH payment intent created for large Enterprise payments."""
        from app.services.stripe_service import StripeService

        svc = StripeService(api_key="sk_test_abc123")

        with patch.object(svc, "_create_payment_intent", return_value={
            "id": "pi_ach_001",
            "status": "requires_payment_method",
            "amount": 399900,  # $3,999.00 in cents
            "currency": "usd",
            "payment_method_types": ["us_bank_account"],
        }):
            result = await svc.create_ach_payment_intent(
                amount_usd=3999,
                clinic_id="clinic_test_001",
                description="Carenova Enterprise — Monthly",
            )

        assert result["success"] is True
        assert result["amount_cents"] == 399900
        assert "us_bank_account" in result["payment_method_types"]

    def test_ach_is_default_for_enterprise(self):
        """ACH is the default payment method for Enterprise — avoids card fees."""
        from app.services.stripe_service import StripeService

        svc = StripeService(api_key="sk_test_abc123")
        assert svc.default_payment_method == "us_bank_account"


class TestStripeInvoicing:

    @pytest.mark.asyncio
    async def test_create_net30_invoice(self):
        """NET-30 invoice created for Enterprise hospital systems."""
        from app.services.stripe_service import StripeService

        svc = StripeService(api_key="sk_test_abc123")

        with patch.object(svc, "_create_invoice", return_value={
            "id": "inv_001",
            "status": "draft",
            "amount_due": 399900,
            "due_date": 1753920000,  # 30 days from now
            "collection_method": "send_invoice",
        }):
            result = await svc.create_net30_invoice(
                customer_id="cus_enterprise_001",
                amount_usd=3999,
                description="Carenova Enterprise — July 2026",
            )

        assert result["success"] is True
        assert result["invoice_id"] == "inv_001"
        assert result["payment_terms"] == "net_30"

    @pytest.mark.asyncio
    async def test_invoice_failure_returns_error(self):
        """Invoice creation failure returns error — never crashes."""
        from app.services.stripe_service import StripeService

        svc = StripeService(api_key="sk_test_abc123")

        with patch.object(svc, "_create_invoice", side_effect=Exception("Stripe API error")):
            result = await svc.create_net30_invoice(
                customer_id="cus_001",
                amount_usd=3999,
                description="Test",
            )

        assert result["success"] is False
        assert "error" in result


class TestStripeWebhookRouter:

    def test_stripe_webhook_endpoint_exists(self):
        """Stripe webhook endpoint registered in billing router."""
        from app.routers.billing import router
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)

        response = client.post(
            "/billing/stripe/webhook",
            json={"type": "payment_intent.succeeded"},
            headers={"stripe-signature": "skip_for_test"},
        )
        assert response.status_code != 404

    def test_payment_succeeded_event_handled(self):
        """payment_intent.succeeded triggers subscription activation."""
        from app.routers.billing import router
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)

        payload = {
            "type": "payment_intent.succeeded",
            "data": {
                "object": {
                    "id": "pi_001",
                    "amount": 399900,
                    "metadata": {"clinic_id": "clinic_test_001"},
                }
            }
        }

        with patch("app.routers.billing.handle_stripe_payment_succeeded") as mock_handler:
            mock_handler.return_value = {"activated": True}
            response = client.post(
                "/billing/stripe/webhook",
                json=payload,
                headers={"stripe-signature": "skip_for_test"},
            )

        assert response.status_code == 200

    def test_subscription_deleted_event_handled(self):
        """customer.subscription.deleted deactivates clinic."""
        from app.routers.billing import router
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)

        payload = {
            "type": "customer.subscription.deleted",
            "data": {
                "object": {
                    "id": "sub_stripe_001",
                    "metadata": {"clinic_id": "clinic_test_001"},
                }
            }
        }

        with patch("app.routers.billing.handle_stripe_subscription_deleted") as mock_handler:
            mock_handler.return_value = {"deactivated": True}
            response = client.post(
                "/billing/stripe/webhook",
                json=payload,
                headers={"stripe-signature": "skip_for_test"},
            )

        assert response.status_code == 200


class TestBillingRouterStack:

    def test_all_three_payment_providers_in_config(self):
        """Config has keys for all three payment providers."""
        from app.config import settings
        # LemonSqueezy
        assert settings.lemonsqueezy_store_id == "247127"
        # Paystack
        assert hasattr(settings, "paystack_secret_key")
        # Stripe
        assert hasattr(settings, "stripe_secret_key")
        assert hasattr(settings, "stripe_webhook_secret")

    def test_payment_provider_routing_logic(self):
        """
        Correct provider selected based on plan tier and region.
        Starter/Pro/Growth US → LemonSqueezy
        Enterprise US         → Stripe
        Nigeria               → Paystack
        """
        from app.services.billing_router import select_payment_provider

        assert select_payment_provider(tier="starter", country="US") == "lemonsqueezy"
        assert select_payment_provider(tier="pro", country="US") == "lemonsqueezy"
        assert select_payment_provider(tier="growth", country="US") == "lemonsqueezy"
        assert select_payment_provider(tier="enterprise", country="US") == "stripe"
        assert select_payment_provider(tier="starter", country="NG") == "paystack"
        assert select_payment_provider(tier="pro", country="NG") == "paystack"
        assert select_payment_provider(tier="enterprise", country="NG") == "paystack"
