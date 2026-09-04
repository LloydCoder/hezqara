"""
Auth + Billing Tests — Sprint 15
TDD RED phase.

Clerk handles multi-tenant auth — one Organisation per clinic.
LemonSqueezy handles billing webhooks for US clinics.
Paystack handles billing for Nigeria.

Every clinic is isolated via Clerk Organisation ID.
Billing state maps to feature access (plan tier).
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient


class TestClerkAuthMiddleware:

    def test_clerk_auth_module_can_be_imported(self):
        from app.security.clerk_auth import verify_clerk_token
        assert verify_clerk_token is not None

    def test_get_clinic_id_from_token_returns_org_id(self):
        """Extracts clinic_id (Clerk org ID) from JWT claims."""
        from app.security.clerk_auth import extract_clinic_id

        mock_claims = {
            "sub": "user_abc123",
            "org_id": "org_clinic_001",
            "org_role": "admin",
        }

        clinic_id = extract_clinic_id(mock_claims)
        assert clinic_id == "org_clinic_001"

    def test_missing_org_id_raises_error(self):
        """Token without org_id is rejected — personal tokens not allowed."""
        from app.security.clerk_auth import extract_clinic_id
        import pytest

        mock_claims = {"sub": "user_abc123"}

        with pytest.raises(ValueError, match="org_id"):
            extract_clinic_id(mock_claims)

    def test_extract_user_role_from_claims(self):
        """Extracts user role for RBAC."""
        from app.security.clerk_auth import extract_user_role

        claims = {"org_role": "admin"}
        assert extract_user_role(claims) == "admin"

    def test_member_role_extracted_correctly(self):
        from app.security.clerk_auth import extract_user_role

        claims = {"org_role": "member"}
        assert extract_user_role(claims) == "member"


class TestLemonSqueezyBilling:

    def test_billing_module_can_be_imported(self):
        from app.services.billing import BillingService
        assert BillingService is not None

    def test_billing_service_requires_api_key(self):
        from app.services.billing import BillingService
        with pytest.raises(TypeError):
            BillingService()

    def test_billing_service_stores_store_id(self):
        from app.services.billing import BillingService
        svc = BillingService(api_key="test_key", store_id="247127")
        assert svc.store_id == "247127"

    @pytest.mark.asyncio
    async def test_get_subscription_returns_plan_tier(self):
        """Maps LemonSqueezy variant to plan tier."""
        from app.services.billing import BillingService

        svc = BillingService(api_key="test_key", store_id="247127")

        with patch.object(svc, "_get_subscription", return_value={
            "status": "active",
            "variant_id": "var_pro_001",
            "variant_name": "Pro",
        }):
            result = await svc.get_clinic_subscription(
                subscription_id="sub_abc123"
            )

        assert result["active"] is True
        assert result["plan_tier"] == "pro"

    @pytest.mark.asyncio
    async def test_inactive_subscription_blocks_access(self):
        """Cancelled subscription returns active=False."""
        from app.services.billing import BillingService

        svc = BillingService(api_key="test_key", store_id="247127")

        with patch.object(svc, "_get_subscription", return_value={
            "status": "cancelled",
            "variant_name": "Starter",
        }):
            result = await svc.get_clinic_subscription(
                subscription_id="sub_abc123"
            )

        assert result["active"] is False

    def test_plan_tier_from_variant_name_starter(self):
        from app.services.billing import BillingService

        svc = BillingService(api_key="test_key", store_id="247127")
        assert svc.variant_to_tier("Starter") == "starter"

    def test_plan_tier_from_variant_name_pro(self):
        from app.services.billing import BillingService

        svc = BillingService(api_key="test_key", store_id="247127")
        assert svc.variant_to_tier("Pro") == "pro"

    def test_plan_tier_from_variant_name_growth(self):
        from app.services.billing import BillingService

        svc = BillingService(api_key="test_key", store_id="247127")
        assert svc.variant_to_tier("Growth") == "growth"

    def test_plan_tier_from_variant_name_enterprise(self):
        from app.services.billing import BillingService

        svc = BillingService(api_key="test_key", store_id="247127")
        assert svc.variant_to_tier("Enterprise") == "enterprise"


class TestBillingWebhookRouter:

    def test_billing_router_can_be_imported(self):
        from app.routers.billing import router
        assert router is not None

    def test_webhook_endpoint_exists(self):
        from app.routers.billing import router
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)

        response = client.post(
            "/billing/webhook",
            json={"meta": {"event_name": "subscription_created"}},
            headers={"x-signature": "skip_for_test"},
        )
        assert response.status_code != 404

    def test_subscription_created_event_handled(self):
        from app.routers.billing import router
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)

        payload = {
            "meta": {
                "event_name": "subscription_created",
                "custom_data": {"clinic_id": "clinic_test_001"},
            },
            "data": {
                "attributes": {
                    "status": "active",
                    "variant_name": "Pro",
                    "subscription_id": "sub_001",
                }
            }
        }

        with patch("app.routers.billing.handle_subscription_created") as mock_handler:
            mock_handler.return_value = {"updated": True}
            response = client.post(
                "/billing/webhook",
                json=payload,
                headers={"x-signature": "skip_for_test"},
            )

        assert response.status_code == 200

    def test_subscription_cancelled_event_handled(self):
        from app.routers.billing import router
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)

        payload = {
            "meta": {
                "event_name": "subscription_cancelled",
                "custom_data": {"clinic_id": "clinic_test_001"},
            },
            "data": {
                "attributes": {
                    "status": "cancelled",
                    "variant_name": "Pro",
                }
            }
        }

        with patch("app.routers.billing.handle_subscription_cancelled") as mock_handler:
            mock_handler.return_value = {"updated": True}
            response = client.post(
                "/billing/webhook",
                json=payload,
                headers={"x-signature": "skip_for_test"},
            )

        assert response.status_code == 200


class TestPaystackBilling:

    def test_paystack_service_can_be_imported(self):
        from app.services.paystack import PaystackService
        assert PaystackService is not None

    def test_paystack_requires_secret_key(self):
        from app.services.paystack import PaystackService
        with pytest.raises(TypeError):
            PaystackService()

    def test_paystack_stores_secret_key(self):
        from app.services.paystack import PaystackService
        svc = PaystackService(secret_key="sk_test_abc")
        assert svc.secret_key == "sk_test_abc"

    @pytest.mark.asyncio
    async def test_verify_paystack_payment_returns_success(self):
        """Paystack payment verification returns success for valid reference."""
        from app.services.paystack import PaystackService

        svc = PaystackService(secret_key="sk_test_abc")

        with patch.object(svc, "_verify_reference", return_value={
            "status": True,
            "data": {
                "status": "success",
                "amount": 5000000,  # NGN 50,000 in kobo
                "reference": "REF_001",
            }
        }):
            result = await svc.verify_payment(reference="REF_001")

        assert result["success"] is True
        assert result["amount_ngn"] == 50000
