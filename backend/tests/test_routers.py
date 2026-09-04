"""
Router Completeness Tests — all API endpoints registered and responding.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch


@pytest.fixture
def client():
    from app.main import app
    return TestClient(app)


class TestAllRoutersRegistered:

    def test_health_endpoint(self, client):
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"

    def test_agents_list_endpoint(self, client):
        r = client.get("/agents?clinic_id=clinic_test_001")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        assert len(data) == 10  # All 10 agents

    def test_agents_get_endpoint(self, client):
        r = client.get("/agents/reception?clinic_id=clinic_test_001")
        assert r.status_code == 200
        assert r.json()["id"] == "reception"

    def test_agents_toggle_endpoint(self, client):
        r = client.post("/agents/scheduling/toggle", json={
            "clinic_id": "clinic_test_001", "enabled": False
        })
        assert r.status_code == 200
        assert r.json()["updated"] is True

    def test_agents_unknown_type_returns_404(self, client):
        r = client.get("/agents/nonexistent?clinic_id=clinic_001")
        assert r.status_code == 404

    def test_calls_list_endpoint(self, client):
        r = client.get("/calls?clinic_id=clinic_test_001")
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_appointments_list_endpoint(self, client):
        r = client.get("/appointments?clinic_id=clinic_test_001")
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_appointments_cancel_endpoint(self, client):
        r = client.post("/appointments/APT001/cancel", json={"reason": "Patient request"})
        assert r.status_code == 200

    def test_patients_list_endpoint(self, client):
        r = client.get("/patients?clinic_id=clinic_test_001")
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_insurance_verify_endpoint(self, client):
        r = client.post("/insurance/verify", json={
            "patient_id": "PAT_001",
            "member_id": "BCB123",
            "date_of_service": "2026-07-01",
        })
        assert r.status_code == 200

    def test_prior_auth_list_endpoint(self, client):
        r = client.get("/prior-auth?clinic_id=clinic_test_001")
        assert r.status_code == 200

    def test_prior_auth_status_endpoint(self, client):
        r = client.get("/prior-auth/PA-001/status")
        assert r.status_code == 200

    def test_recalls_list_endpoint(self, client):
        r = client.get("/recalls?clinic_id=clinic_test_001")
        assert r.status_code == 200

    def test_recalls_launch_endpoint(self, client):
        r = client.post("/recalls/launch", json={
            "clinic_id": "clinic_test_001",
            "recall_type": "annual_checkup",
        })
        assert r.status_code == 200
        assert r.json()["launched"] is True

    def test_referrals_list_endpoint(self, client):
        r = client.get("/referrals?clinic_id=clinic_test_001")
        assert r.status_code == 200

    def test_analytics_summary_endpoint(self, client):
        r = client.get("/analytics/summary?clinic_id=clinic_test_001&period=today")
        assert r.status_code == 200
        data = r.json()
        assert "total_calls" in data
        assert "total_appointments_booked" in data
        assert "total_cost_savings_usd" in data

    def test_analytics_daily_endpoint(self, client):
        r = client.get("/analytics/daily?clinic_id=clinic_test_001&date=2026-07-01")
        assert r.status_code == 200

    def test_billing_webhook_endpoint(self, client):
        r = client.post("/billing/webhook",
            json={"meta": {"event_name": "subscription_created", "custom_data": {"clinic_id": "c1"}}, "data": {"attributes": {}}},
            headers={"x-signature": "skip_for_test"})
        assert r.status_code == 200

    def test_stripe_webhook_endpoint(self, client):
        r = client.post("/billing/stripe/webhook",
            json={"type": "payment_intent.succeeded", "data": {"object": {"metadata": {}}}},
            headers={"stripe-signature": "skip_for_test"})
        assert r.status_code == 200

    def test_voice_webhook_endpoint(self, client):
        r = client.post("/voice/webhook",
            json={"event": "call_started", "call": {"call_id": "c1", "from_number": "+1", "metadata": {"clinic_id": "c1"}}},
            headers={"x-retell-signature": "skip_for_test"})
        assert r.status_code == 200

    def test_whatsapp_webhook_verify_endpoint(self, client):
        r = client.get("/whatsapp/webhook", params={
            "hub.mode": "subscribe",
            "hub.challenge": "test",
            "hub.verify_token": "wrong",
        })
        assert r.status_code in [200, 403]  # Valid token or rejected

    def test_whatsapp_inbound_endpoint(self, client):
        with patch("app.routers.whatsapp.handle_inbound_message") as m:
            m.return_value = {"processed": True}
            r = client.post("/whatsapp/webhook", json={
                "entry": [{"changes": [{"value": {"messages": [{
                    "from": "2348012345678",
                    "id": "wamid.001",
                    "text": {"body": "Hello"},
                    "type": "text",
                    "timestamp": "1751328000",
                }]}}]}]
            })
        assert r.status_code == 200

    def test_all_10_agents_in_registry(self, client):
        """Every defined agent type is returned by the list endpoint."""
        r = client.get("/agents?clinic_id=clinic_test_001")
        ids = [a["id"] for a in r.json()]
        expected = ["reception","scheduling","intake","insurance",
                    "prior_auth","refill","records","referrals","recall","email"]
        for eid in expected:
            assert eid in ids, f"Agent '{eid}' missing from /agents response"
