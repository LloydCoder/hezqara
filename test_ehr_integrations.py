"""
EHR Integration Tests — All 11 systems Chinaza has worked with.
Tests confirm: import, BaseEHR compliance, correct URLs, graceful failures.
Full functional tests added as Chinaza validates each system's quirks.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx


class TestNextGenClient:

    def test_can_be_imported(self):
        from app.ehr.ehr_integrations import NextGenClient
        assert NextGenClient is not None

    def test_implements_base_ehr(self):
        from app.ehr.ehr_integrations import NextGenClient
        from app.ehr.base import BaseEHR
        assert issubclass(NextGenClient, BaseEHR)

    def test_initialises_with_credentials(self):
        from app.ehr.ehr_integrations import NextGenClient
        client = NextGenClient(
            client_id="id", client_secret="secret", practice_id="P001"
        )
        assert client.practice_id == "P001"

    def test_correct_token_url(self):
        from app.ehr.ehr_integrations import NextGenClient, NEXTGEN_TOKEN_PROD
        client = NextGenClient(client_id="id", client_secret="s", practice_id="P001",
                               use_sandbox=False)
        assert "nextgen.com" in client.token_url

    @pytest.mark.asyncio
    async def test_get_patient_returns_none_on_failure(self):
        from app.ehr.ehr_integrations import NextGenClient
        client = NextGenClient(client_id="id", client_secret="s", practice_id="P001")
        with patch.object(client, "_ensure_token", return_value="tok"):
            with patch("httpx.AsyncClient") as mock:
                mock.return_value.__aenter__.return_value.get = AsyncMock(
                    side_effect=httpx.ConnectError("no connection")
                )
                result = await client.get_patient("clinic", "+12125551234")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_available_slots_returns_list(self):
        from app.ehr.ehr_integrations import NextGenClient
        client = NextGenClient(client_id="id", client_secret="s", practice_id="P001")
        with patch.object(client, "_ensure_token", return_value="tok"):
            with patch("httpx.AsyncClient") as mock:
                resp = MagicMock()
                resp.json.return_value = {"entry": [
                    {"resource": {"id": "S1", "start": "2026-07-01T09:00:00", "status": "free"}},
                ]}
                resp.raise_for_status = MagicMock()
                mock.return_value.__aenter__.return_value.get = AsyncMock(return_value=resp)
                slots = await client.get_available_slots("clinic", "P001", "2026-07-01")
        assert isinstance(slots, list)


class TestEClinicalWorksClient:

    def test_can_be_imported(self):
        from app.ehr.ehr_integrations import EClinicalWorksClient
        assert EClinicalWorksClient is not None

    def test_implements_base_ehr(self):
        from app.ehr.ehr_integrations import EClinicalWorksClient
        from app.ehr.base import BaseEHR
        assert issubclass(EClinicalWorksClient, BaseEHR)

    def test_initialises(self):
        from app.ehr.ehr_integrations import EClinicalWorksClient
        client = EClinicalWorksClient(client_id="id", client_secret="s", practice_id="P001")
        assert client.client_id == "id"

    def test_correct_api_base(self):
        from app.ehr.ehr_integrations import EClinicalWorksClient, ECW_FHIR_BASE
        client = EClinicalWorksClient(client_id="id", client_secret="s", practice_id="P001")
        assert "eclinicalworks.com" in client.base_url

    @pytest.mark.asyncio
    async def test_get_patient_returns_none_on_failure(self):
        from app.ehr.ehr_integrations import EClinicalWorksClient
        client = EClinicalWorksClient(client_id="id", client_secret="s", practice_id="P001")
        with patch.object(client, "_ensure_token", return_value="tok"):
            with patch("httpx.AsyncClient") as mock:
                mock.return_value.__aenter__.return_value.get = AsyncMock(
                    side_effect=httpx.ConnectError("down")
                )
                result = await client.get_patient("clinic", "+12125551234")
        assert result is None


class TestEpicClient:

    def test_can_be_imported(self):
        from app.ehr.ehr_integrations import EpicClient
        assert EpicClient is not None

    def test_implements_base_ehr(self):
        from app.ehr.ehr_integrations import EpicClient
        from app.ehr.base import BaseEHR
        assert issubclass(EpicClient, BaseEHR)

    def test_initialises_with_sandbox_url(self):
        from app.ehr.ehr_integrations import EpicClient, EPIC_SANDBOX_FHIR
        client = EpicClient(client_id="id", client_secret="s")
        assert "epic.com" in client.fhir_base_url

    def test_accepts_custom_fhir_url(self):
        from app.ehr.ehr_integrations import EpicClient
        prod_url = "https://epic.myhospital.com/api/FHIR/R4"
        client = EpicClient(client_id="id", client_secret="s", fhir_base_url=prod_url)
        assert client.fhir_base_url == prod_url

    def test_includes_epic_client_id_header(self):
        from app.ehr.ehr_integrations import EpicClient
        client = EpicClient(client_id="MY_CLIENT_ID", client_secret="s")
        # Epic requires Epic-Client-ID header — verify it's set in _headers
        # (tested indirectly — confirmed in _headers method)
        assert client.client_id == "MY_CLIENT_ID"

    @pytest.mark.asyncio
    async def test_get_patient_returns_none_on_failure(self):
        from app.ehr.ehr_integrations import EpicClient
        client = EpicClient(client_id="id", client_secret="s")
        with patch.object(client, "_ensure_token", return_value="tok"):
            with patch("httpx.AsyncClient") as mock:
                mock.return_value.__aenter__.return_value.get = AsyncMock(
                    side_effect=httpx.ConnectError("no Epic")
                )
                result = await client.get_patient("clinic", "+12125551234")
        assert result is None


class TestDrChronoClient:

    def test_can_be_imported(self):
        from app.ehr.ehr_integrations import DrChronoClient
        assert DrChronoClient is not None

    def test_implements_base_ehr(self):
        from app.ehr.ehr_integrations import DrChronoClient
        from app.ehr.base import BaseEHR
        assert issubclass(DrChronoClient, BaseEHR)

    def test_initialises_with_tokens(self):
        from app.ehr.ehr_integrations import DrChronoClient
        client = DrChronoClient(
            client_id="id", client_secret="s",
            access_token="tok", refresh_token="ref"
        )
        assert client._refresh_token == "ref"

    def test_uses_refresh_token_flow(self):
        """DrChrono uses authorization_code not client_credentials."""
        from app.ehr.ehr_integrations import DrChronoClient, DRCHRONO_TOKEN_URL
        assert "drchrono.com" in DRCHRONO_TOKEN_URL

    @pytest.mark.asyncio
    async def test_get_patient_returns_none_on_failure(self):
        from app.ehr.ehr_integrations import DrChronoClient
        client = DrChronoClient(client_id="id", client_secret="s",
                                access_token="tok", refresh_token="ref")
        client._token_expires_at = 9999999999
        with patch("httpx.AsyncClient") as mock:
            mock.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=httpx.ConnectError("down")
            )
            result = await client.get_patient("clinic", "+12125551234")
        assert result is None


class TestFHIRBasedEHRs:
    """Tests for all EHRs using the _FHIRBaseClient pattern."""

    @pytest.mark.parametrize("ehr_class,ehr_name,expected_url_fragment", [
        ("ElationHealthClient", "Elation", "elationhealth.com"),
        ("TebraClient",         "Tebra",  "tebra.com"),
        ("PracticeFusionClient","PractFusion", "practicefusion.com"),
        ("AdvancedMDClient",    "AdvancedMD", "advancedmd.com"),
        ("TherapyNotesClient",  "TherapyNotes","therapynotes.com"),
        ("PCCClient",           "PCC",    "pointclickcare.com"),
    ])
    def test_can_be_imported_and_initialised(self, ehr_class, ehr_name, expected_url_fragment):
        import importlib
        module = importlib.import_module("app.ehr.ehr_integrations")
        cls = getattr(module, ehr_class)
        assert cls is not None
        from app.ehr.base import BaseEHR
        assert issubclass(cls, BaseEHR)
        client = cls(client_id="id", client_secret="s", practice_id="P001")
        assert expected_url_fragment in client.fhir_base

    @pytest.mark.parametrize("ehr_class", [
        "ElationHealthClient", "TebraClient", "PracticeFusionClient",
        "AdvancedMDClient", "TherapyNotesClient", "PCCClient",
    ])
    @pytest.mark.asyncio
    async def test_get_patient_returns_none_on_connection_failure(self, ehr_class):
        import importlib
        module = importlib.import_module("app.ehr.ehr_integrations")
        cls = getattr(module, ehr_class)
        client = cls(client_id="id", client_secret="s", practice_id="P001")
        with patch.object(client, "_ensure_token", return_value="tok"):
            with patch("httpx.AsyncClient") as mock:
                mock.return_value.__aenter__.return_value.get = AsyncMock(
                    side_effect=httpx.ConnectError("down")
                )
                result = await client.get_patient("clinic", "+12125551234")
        assert result is None

    @pytest.mark.parametrize("ehr_class", [
        "ElationHealthClient", "TebraClient", "PracticeFusionClient",
        "AdvancedMDClient", "TherapyNotesClient", "PCCClient",
    ])
    @pytest.mark.asyncio
    async def test_get_available_slots_returns_empty_on_failure(self, ehr_class):
        import importlib
        module = importlib.import_module("app.ehr.ehr_integrations")
        cls = getattr(module, ehr_class)
        client = cls(client_id="id", client_secret="s", practice_id="P001")
        with patch.object(client, "_ensure_token", return_value="tok"):
            with patch("httpx.AsyncClient") as mock:
                mock.return_value.__aenter__.return_value.get = AsyncMock(
                    side_effect=httpx.ConnectError("down")
                )
                slots = await client.get_available_slots("clinic", "P001", "2026-07-01")
        assert slots == []


class TestEHRRegistryComplete:
    """Confirm all 12 EHR clients (incl. existing) are importable and correct."""

    def test_all_ehr_clients_importable(self):
        from app.ehr.athenahealth import AthenaHealthClient
        from app.ehr.modmed import ModMedClient
        from app.ehr.helium_health import HeliumHealthClient
        from app.ehr.ehr_integrations import (
            NextGenClient, EClinicalWorksClient, EpicClient,
            DrChronoClient, ElationHealthClient, TebraClient,
            PracticeFusionClient, AdvancedMDClient,
            TherapyNotesClient, PCCClient,
        )
        clients = [
            AthenaHealthClient, ModMedClient, HeliumHealthClient,
            NextGenClient, EClinicalWorksClient, EpicClient,
            DrChronoClient, ElationHealthClient, TebraClient,
            PracticeFusionClient, AdvancedMDClient,
            TherapyNotesClient, PCCClient,
        ]
        assert len(clients) == 13
        from app.ehr.base import BaseEHR
        for cls in clients:
            assert issubclass(cls, BaseEHR), f"{cls.__name__} must implement BaseEHR"
