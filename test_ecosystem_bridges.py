"""
Full Ecosystem Bridge Tests — Sprint 22
TDD RED phase.

All 20 Tinlance products wired to Carenova.
Governing rule: nothing connects product-to-product directly.
Everything routes through FusionOps as technical hub.
AI Shield is the only exception — surveillance infrastructure.

Tier 1 (Critical): FusionOps, AI Shield, ThreatFade, ResilientAI ← Already built Phase 3
Tier 2 (High):     FadeReach, HezCast, ResonaForge, FederX, Olvrix, Olvrix Widgets, KalevioAI
Tier 3 (Medium):   ReconOS OFE, BugFlow, TwinGuard, FDSE Toolkit, FadeForge
Pattern sharing:   RealtyScreen AI, GiftMode, Web-Temify, Voquo, HezVanguard

All bridges: fire-and-forget async, graceful fallback, queue-and-replay when offline.
"""
import pytest
from unittest.mock import AsyncMock, patch
import httpx


# ── Tier 2 Bridge Tests ───────────────────────────────────────────────────────

class TestFadeReachBridge:
    """FadeReach — patient recall + outreach automation hub."""

    def test_fadereach_bridge_can_be_imported(self):
        from app.bridges.fadereach import FadeReachBridge
        assert FadeReachBridge is not None

    def test_fadereach_bridge_stores_url(self):
        from app.bridges.fadereach import FadeReachBridge
        bridge = FadeReachBridge(url="https://fadereach.ai", api_key="key")
        assert bridge.url == "https://fadereach.ai"

    @pytest.mark.asyncio
    async def test_fadereach_triggers_onboarding_sequence(self):
        """New clinic payment → FadeReach onboarding sequence fires."""
        from app.bridges.fadereach import FadeReachBridge

        bridge = FadeReachBridge(url="https://fadereach.ai", api_key="key")
        with patch.object(bridge, "_post", return_value={"queued": True}):
            result = await bridge.trigger_sequence(
                sequence_id="clinic_onboarding",
                clinic_id="clinic_test_001",
                contact_email="billing@familycare.com",
                metadata={"plan_tier": "pro"},
            )
        assert result["sent"] is True

    @pytest.mark.asyncio
    async def test_fadereach_triggers_recall_campaign(self):
        """Recall agent fires FadeReach for multi-channel outreach."""
        from app.bridges.fadereach import FadeReachBridge

        bridge = FadeReachBridge(url="https://fadereach.ai", api_key="key")
        with patch.object(bridge, "_post", return_value={"queued": True}):
            result = await bridge.trigger_recall_campaign(
                clinic_id="clinic_test_001",
                campaign_type="annual_checkup",
                patient_count=47,
            )
        assert result["sent"] is True

    @pytest.mark.asyncio
    async def test_fadereach_fails_gracefully(self):
        """FadeReach down never blocks patient care."""
        from app.bridges.fadereach import FadeReachBridge

        bridge = FadeReachBridge(url="https://fadereach.ai", api_key="key")
        with patch.object(bridge, "_post", side_effect=Exception("timeout")):
            result = await bridge.trigger_sequence(
                sequence_id="onboarding",
                clinic_id="clinic_001",
                contact_email="test@test.com",
            )
        assert result["sent"] is False
        assert "error" in result


class TestHezCastBridge:
    """HezCast — patient communication content engine."""

    def test_hezcast_bridge_can_be_imported(self):
        from app.bridges.hezcast import HezCastBridge
        assert HezCastBridge is not None

    @pytest.mark.asyncio
    async def test_hezcast_generates_patient_content(self):
        """HezCast generates appointment reminder content."""
        from app.bridges.hezcast import HezCastBridge

        bridge = HezCastBridge(url="https://hezcast.tinlance.com", api_key="key")
        with patch.object(bridge, "_post", return_value={
            "content": "Your appointment is tomorrow at 9 AM. See you then!",
            "content_id": "cnt_001",
        }):
            result = await bridge.generate_content(
                content_type="appointment_reminder",
                clinic_id="clinic_test_001",
                variables={"patient_name": "Maria", "datetime": "tomorrow 9 AM"},
            )
        assert result["sent"] is True
        assert "content" in result

    @pytest.mark.asyncio
    async def test_hezcast_fails_gracefully(self):
        from app.bridges.hezcast import HezCastBridge
        bridge = HezCastBridge(url="https://hezcast.tinlance.com", api_key="key")
        with patch.object(bridge, "_post", side_effect=httpx.ConnectError("down")):
            result = await bridge.generate_content(
                content_type="recall_sms",
                clinic_id="clinic_001",
                variables={},
            )
        assert result["sent"] is False


class TestKalevioAIBridge:
    """KalevioAI — HIPAA compliance intelligence (live at kalevio.tinlance.com)."""

    def test_kalevioai_bridge_can_be_imported(self):
        from app.bridges.kalevioai import KalevioAIBridge
        assert KalevioAIBridge is not None

    @pytest.mark.asyncio
    async def test_kalevioai_runs_compliance_check(self):
        """KalevioAI validates Carenova clinic's HIPAA posture."""
        from app.bridges.kalevioai import KalevioAIBridge

        bridge = KalevioAIBridge(
            url="https://kalevio.tinlance.com",
            api_key="key",
        )
        with patch.object(bridge, "_post", return_value={
            "score": 87,
            "status": "compliant",
            "findings": [],
        }):
            result = await bridge.run_compliance_check(
                clinic_id="clinic_test_001",
                check_type="hipaa_full",
            )
        assert result["sent"] is True
        assert result["score"] == 87

    @pytest.mark.asyncio
    async def test_kalevioai_fails_gracefully(self):
        from app.bridges.kalevioai import KalevioAIBridge
        bridge = KalevioAIBridge(url="https://kalevio.tinlance.com", api_key="key")
        with patch.object(bridge, "_post", side_effect=Exception("timeout")):
            result = await bridge.run_compliance_check(
                clinic_id="clinic_001",
                check_type="hipaa_full",
            )
        assert result["sent"] is False


class TestOlvrixBridge:
    """Olvrix — clinic lead prospecting ('hiring receptionist' signal scraping)."""

    def test_olvrix_bridge_can_be_imported(self):
        from app.bridges.olvrix import OlvrixBridge
        assert OlvrixBridge is not None

    @pytest.mark.asyncio
    async def test_olvrix_fires_lead_converted_event(self):
        """Clinic payment → LEAD_CONVERTED event to Olvrix."""
        from app.bridges.olvrix import OlvrixBridge

        bridge = OlvrixBridge(url="https://olvrix.tinlance.com", api_key="key")
        with patch.object(bridge, "_post", return_value={"received": True}):
            result = await bridge.fire_event(
                event_type="LEAD_CONVERTED",
                clinic_id="clinic_test_001",
                metadata={"plan_tier": "pro", "mrr": 999},
            )
        assert result["sent"] is True

    @pytest.mark.asyncio
    async def test_olvrix_fails_gracefully(self):
        from app.bridges.olvrix import OlvrixBridge
        bridge = OlvrixBridge(url="https://olvrix.tinlance.com", api_key="key")
        with patch.object(bridge, "_post", side_effect=Exception("offline")):
            result = await bridge.fire_event(
                event_type="LEAD_CONVERTED",
                clinic_id="clinic_001",
                metadata={},
            )
        assert result["sent"] is False


class TestResonaForgeBridge:
    """ResonaForge — brand authority intelligence."""

    def test_resonaforge_bridge_can_be_imported(self):
        from app.bridges.resonaforge import ResonaForgeBridge
        assert ResonaForgeBridge is not None

    @pytest.mark.asyncio
    async def test_resonaforge_sends_brand_event(self):
        from app.bridges.resonaforge import ResonaForgeBridge
        bridge = ResonaForgeBridge(url="https://resonaforge.tinlance.com", api_key="key")
        with patch.object(bridge, "_post", return_value={"received": True}):
            result = await bridge.send_brand_signal(
                signal_type="clinic_onboarded",
                clinic_id="clinic_test_001",
            )
        assert result["sent"] is True


class TestVoquoBridge:
    """Voquo — AI video production (patient education videos)."""

    def test_voquo_bridge_can_be_imported(self):
        from app.bridges.voquo import VoquoBridge
        assert VoquoBridge is not None

    @pytest.mark.asyncio
    async def test_voquo_requests_patient_video(self):
        """Request patient education video generation."""
        from app.bridges.voquo import VoquoBridge
        bridge = VoquoBridge(url="https://voquo.tinlance.com", api_key="key")
        with patch.object(bridge, "_post", return_value={
            "job_id": "vid_001", "status": "queued"
        }):
            result = await bridge.request_video(
                video_type="procedure_explanation",
                clinic_id="clinic_test_001",
                topic="What to expect at your first visit",
            )
        assert result["sent"] is True


# ── Tier 3 Bridge Tests ───────────────────────────────────────────────────────

class TestBugFlowBridge:
    """BugFlow Elite — security audit pipeline."""

    def test_bugflow_bridge_can_be_imported(self):
        from app.bridges.bugflow import BugFlowBridge
        assert BugFlowBridge is not None

    @pytest.mark.asyncio
    async def test_bugflow_triggers_security_scan(self):
        from app.bridges.bugflow import BugFlowBridge
        bridge = BugFlowBridge(url="https://bugflow.tinlance.com", api_key="key")
        with patch.object(bridge, "_post", return_value={
            "scan_id": "scan_001", "status": "queued"
        }):
            result = await bridge.trigger_scan(
                scan_type="owasp_top10",
                target="carenova-backend",
                clinic_id="clinic_test_001",
            )
        assert result["sent"] is True


class TestTwinGuardBridge:
    """TwinGuard — agent containment + destructive action veto."""

    def test_twinguard_bridge_can_be_imported(self):
        from app.bridges.twinguard import TwinGuardBridge
        assert TwinGuardBridge is not None

    @pytest.mark.asyncio
    async def test_twinguard_validates_destructive_action(self):
        """TwinGuard votes on potentially destructive agent actions."""
        from app.bridges.twinguard import TwinGuardBridge
        bridge = TwinGuardBridge(url="https://twinguard.tinlance.com", api_key="key")
        with patch.object(bridge, "_post", return_value={
            "approved": True,
            "confidence": 0.92,
            "veto": False,
        }):
            result = await bridge.validate_action(
                action_type="bulk_appointment_cancel",
                clinic_id="clinic_test_001",
                payload={"count": 3, "reason": "provider sick"},
            )
        assert result["approved"] is True
        assert result["veto"] is False

    @pytest.mark.asyncio
    async def test_twinguard_vetoes_suspicious_action(self):
        """TwinGuard vetoes actions that look like prompt injection."""
        from app.bridges.twinguard import TwinGuardBridge
        bridge = TwinGuardBridge(url="https://twinguard.tinlance.com", api_key="key")
        with patch.object(bridge, "_post", return_value={
            "approved": False,
            "confidence": 0.98,
            "veto": True,
            "reason": "Destructive bulk delete without authorization",
        }):
            result = await bridge.validate_action(
                action_type="delete_all_patient_records",
                clinic_id="clinic_test_001",
                payload={},
            )
        assert result["veto"] is True

    @pytest.mark.asyncio
    async def test_twinguard_fails_safe_on_timeout(self):
        """TwinGuard timeout = approved (never block patient care)."""
        from app.bridges.twinguard import TwinGuardBridge
        bridge = TwinGuardBridge(url="https://twinguard.tinlance.com", api_key="key")
        with patch.object(bridge, "_post", side_effect=httpx.TimeoutException("timeout")):
            result = await bridge.validate_action(
                action_type="book_appointment",
                clinic_id="clinic_test_001",
                payload={},
            )
        assert result["approved"] is True
        assert result.get("fallback") is True


class TestReconOSBridge:
    """ReconOS OFE — clinic OSINT intelligence."""

    def test_reconos_bridge_can_be_imported(self):
        from app.bridges.reconos import ReconOSBridge
        assert ReconOSBridge is not None

    @pytest.mark.asyncio
    async def test_reconos_fetches_clinic_intelligence(self):
        from app.bridges.reconos import ReconOSBridge
        bridge = ReconOSBridge(url="https://reconos.tinlance.com", api_key="key")
        with patch.object(bridge, "_post", return_value={
            "clinic_name": "Family Care Associates",
            "provider_count": 3,
            "has_ehr": True,
            "hiring_receptionist": True,
        }):
            result = await bridge.fetch_clinic_intel(
                clinic_name="Family Care Associates",
                location="Brooklyn, NY",
            )
        assert result["sent"] is True


# ── Full Ecosystem Bus Extension ──────────────────────────────────────────────

class TestExtendedEcosystemBus:
    """Ecosystem bus routes events to all 20 products."""

    @pytest.mark.asyncio
    async def test_bus_appointment_booked_notifies_fadereach(self):
        """appointment_booked → FadeReach gets confirmation sequence queued."""
        from app.bridges.ecosystem_bus import EcosystemBus

        bus = EcosystemBus()
        with patch.object(bus, "_send_to_fusionops", return_value={"sent": True}):
            await bus.fire(
                event_type="appointment_booked",
                clinic_id="clinic_test_001",
                payload={
                    "appointment_id": "APT001",
                    "patient_id": "PAT_001",
                    "datetime": "2026-07-01T09:00:00",
                },
            )

    @pytest.mark.asyncio
    async def test_bus_subscription_created_notifies_all(self):
        """subscription_created is the most important event — all products notified."""
        from app.bridges.ecosystem_bus import EcosystemBus

        bus = EcosystemBus()
        fired_events = []

        async def mock_fusionops(event_type, clinic_id, payload):
            fired_events.append(event_type)
            return {"sent": True}

        with patch.object(bus, "_send_to_fusionops", side_effect=mock_fusionops):
            await bus.fire(
                event_type="subscription_created",
                clinic_id="clinic_test_001",
                payload={"plan_tier": "pro", "mrr": 999},
            )

        assert "subscription_created" in fired_events

    @pytest.mark.asyncio
    async def test_bus_never_raises_regardless_of_failures(self):
        """Bus must never raise — patient care cannot be blocked."""
        from app.bridges.ecosystem_bus import EcosystemBus

        bus = EcosystemBus()
        with patch.object(bus, "_send_to_fusionops", side_effect=Exception("All bridges down")):
            # Must not raise
            await bus.fire(
                event_type="call_started",
                clinic_id="clinic_test_001",
                payload={},
            )
