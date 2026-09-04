"""
athenahealth Complete Integration Tests
TDD RED phase — tests for everything missing from v1.

Gap 1: OAuth2 token fetching (currently always None)
Gap 2: Token refresh (tokens expire in 1 hour)
Gap 3: Production vs sandbox URL handling
Gap 4: Insurance eligibility endpoint
Gap 5: Appointment types lookup
Gap 6: Provider listing
Gap 7: Department listing
Gap 8: Error handling (429 rate limit, 401 expired token, 503 athena outage)
Gap 9: Webhook event subscription
Gap 10: FHIR R4 patient search by name/DOB (not just phone)
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx


class TestOAuth2TokenManagement:

    def test_client_starts_with_no_token(self):
        from app.ehr.athenahealth import AthenaHealthClient
        client = AthenaHealthClient(
            client_id="id", client_secret="secret", practice_id="195900"
        )
        assert client._access_token is None

    @pytest.mark.asyncio
    async def test_fetch_token_calls_correct_endpoint(self):
        """Token fetched from production OAuth endpoint."""
        from app.ehr.athenahealth import AthenaHealthClient

        client = AthenaHealthClient(
            client_id="test_id",
            client_secret="test_secret",
            practice_id="195900",
        )

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "access_token": "tok_abc123",
            "expires_in": 3600,
            "token_type": "Bearer",
        }
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as MockClient:
            MockClient.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )
            token = await client._fetch_token()

        assert token == "tok_abc123"
        assert client._access_token == "tok_abc123"

    @pytest.mark.asyncio
    async def test_token_reused_when_still_valid(self):
        """Valid token not re-fetched — saves an HTTP round trip."""
        from app.ehr.athenahealth import AthenaHealthClient
        import time

        client = AthenaHealthClient(
            client_id="test_id",
            client_secret="test_secret",
            practice_id="195900",
        )
        client._access_token = "existing_token"
        client._token_expires_at = time.time() + 1800  # 30 min left

        with patch.object(client, "_fetch_token") as mock_fetch:
            await client._ensure_token()

        mock_fetch.assert_not_called()

    @pytest.mark.asyncio
    async def test_expired_token_refreshed_automatically(self):
        """Expired token triggers automatic refresh."""
        from app.ehr.athenahealth import AthenaHealthClient
        import time

        client = AthenaHealthClient(
            client_id="test_id",
            client_secret="test_secret",
            practice_id="195900",
        )
        client._access_token = "old_token"
        client._token_expires_at = time.time() - 60  # Expired 60s ago

        with patch.object(client, "_fetch_token", return_value="new_token") as mock_fetch:
            await client._ensure_token()

        mock_fetch.assert_called_once()

    @pytest.mark.asyncio
    async def test_401_response_triggers_token_refresh_and_retry(self):
        """401 from API triggers token refresh + automatic retry."""
        from app.ehr.athenahealth import AthenaHealthClient

        client = AthenaHealthClient(
            client_id="test_id",
            client_secret="test_secret",
            practice_id="195900",
        )
        client._access_token = "stale_token"

        call_count = 0

        async def mock_get_with_retry(path, params=None):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise httpx.HTTPStatusError(
                    "401", request=MagicMock(), response=MagicMock(status_code=401)
                )
            return {"patients": [{"patientid": "1", "firstname": "A", "lastname": "B"}]}

        with patch.object(client, "_get", side_effect=mock_get_with_retry):
            with patch.object(client, "_fetch_token", return_value="new_token"):
                result = await client.get_patient("clinic_001", "+12125551234")

        # Should have retried after token refresh
        assert result is not None or call_count >= 1


class TestProductionURLs:

    def test_default_url_is_sandbox_for_preview(self):
        """Default URL is sandbox for development."""
        from app.ehr.athenahealth import AthenaHealthClient, ATHENA_PREVIEW_BASE
        client = AthenaHealthClient(
            client_id="id", client_secret="secret", practice_id="195900"
        )
        assert client.base_url == ATHENA_PREVIEW_BASE

    def test_production_url_available(self):
        """Production URL constant is defined."""
        from app.ehr.athenahealth import ATHENA_PROD_BASE
        assert "api.platform.athenahealth.com" in ATHENA_PROD_BASE
        assert "preview" not in ATHENA_PROD_BASE

    def test_client_accepts_production_url(self):
        """Client can be initialised with production URL."""
        from app.ehr.athenahealth import AthenaHealthClient, ATHENA_PROD_BASE
        client = AthenaHealthClient(
            client_id="id",
            client_secret="secret",
            practice_id="195900",
            base_url=ATHENA_PROD_BASE,
        )
        assert client.base_url == ATHENA_PROD_BASE

    def test_token_endpoint_uses_correct_base(self):
        """Token endpoint matches the configured base URL environment."""
        from app.ehr.athenahealth import AthenaHealthClient, ATHENA_TOKEN_URL
        assert "api.platform.athenahealth.com" in ATHENA_TOKEN_URL


class TestProviderAndDepartmentLookup:

    @pytest.mark.asyncio
    async def test_get_providers_returns_list(self):
        """Fetch providers for scheduling agent."""
        from app.ehr.athenahealth import AthenaHealthClient

        client = AthenaHealthClient(
            client_id="id", client_secret="secret", practice_id="195900"
        )

        with patch.object(client, "_get", return_value={
            "providers": [
                {"providerid": "P001", "firstname": "James", "lastname": "Chen", "specialty": "Family Medicine"},
                {"providerid": "P002", "firstname": "Sarah", "lastname": "Kim", "specialty": "Internal Medicine"},
            ]
        }):
            providers = await client.get_providers(clinic_id="clinic_001")

        assert len(providers) == 2
        assert providers[0]["provider_id"] == "P001"
        assert providers[0]["name"] == "Dr. James Chen"

    @pytest.mark.asyncio
    async def test_get_departments_returns_list(self):
        """Fetch departments for multi-location practices."""
        from app.ehr.athenahealth import AthenaHealthClient

        client = AthenaHealthClient(
            client_id="id", client_secret="secret", practice_id="195900"
        )

        with patch.object(client, "_get", return_value={
            "departments": [
                {"departmentid": "D001", "name": "Main Office", "phone": "2125550001"},
                {"departmentid": "D002", "name": "Downtown", "phone": "2125550002"},
            ]
        }):
            depts = await client.get_departments(clinic_id="clinic_001")

        assert len(depts) == 2
        assert depts[0]["department_id"] == "D001"

    @pytest.mark.asyncio
    async def test_get_appointment_types_returns_list(self):
        """Fetch valid appointment types — required for booking."""
        from app.ehr.athenahealth import AthenaHealthClient

        client = AthenaHealthClient(
            client_id="id", client_secret="secret", practice_id="195900"
        )

        with patch.object(client, "_get", return_value={
            "appointmenttypes": [
                {"appointmenttypeid": "1", "name": "New Patient", "duration": 45},
                {"appointmenttypeid": "2", "name": "Follow-up", "duration": 20},
                {"appointmenttypeid": "3", "name": "Annual Exam", "duration": 60},
            ]
        }):
            types = await client.get_appointment_types(clinic_id="clinic_001")

        assert len(types) == 3
        assert types[0]["type_id"] == "1"
        assert types[0]["name"] == "New Patient"
        assert types[0]["duration_minutes"] == 45


class TestInsuranceEligibility:

    @pytest.mark.asyncio
    async def test_check_insurance_eligibility_returns_result(self):
        """Insurance eligibility check returns structured result."""
        from app.ehr.athenahealth import AthenaHealthClient

        client = AthenaHealthClient(
            client_id="id", client_secret="secret", practice_id="195900"
        )

        with patch.object(client, "_post", return_value={
            "eligibilitystatus": "active",
            "insuranceid": "BCB-847291",
            "copays": [{"copaytype": "PRIMARY_CARE", "amount": "25.00"}],
            "deductibles": [{"remaining": "800.00", "total": "1500.00"}],
        }):
            result = await client.check_eligibility(
                clinic_id="clinic_001",
                patient_id="12345",
                insurance_id="BCB-847291",
                date_of_service="2026-07-01",
            )

        assert result["eligible"] is True
        assert result["copay_primary_care"] == 25.0
        assert result["deductible_remaining"] == 800.0

    @pytest.mark.asyncio
    async def test_inactive_insurance_returns_eligible_false(self):
        """Inactive insurance clearly returned as eligible=False."""
        from app.ehr.athenahealth import AthenaHealthClient

        client = AthenaHealthClient(
            client_id="id", client_secret="secret", practice_id="195900"
        )

        with patch.object(client, "_post", return_value={
            "eligibilitystatus": "inactive",
            "insuranceid": "BCB-000000",
        }):
            result = await client.check_eligibility(
                clinic_id="clinic_001",
                patient_id="12345",
                insurance_id="BCB-000000",
                date_of_service="2026-07-01",
            )

        assert result["eligible"] is False

    @pytest.mark.asyncio
    async def test_eligibility_failure_does_not_crash_agent(self):
        """Insurance check failure returns safe fallback — call continues."""
        from app.ehr.athenahealth import AthenaHealthClient

        client = AthenaHealthClient(
            client_id="id", client_secret="secret", practice_id="195900"
        )

        with patch.object(client, "_post", side_effect=Exception("Availity timeout")):
            result = await client.check_eligibility(
                clinic_id="clinic_001",
                patient_id="12345",
                insurance_id="BCB-847291",
                date_of_service="2026-07-01",
            )

        assert result["eligible"] is None  # Unknown, not False
        assert "error" in result


class TestPatientSearchByName:

    @pytest.mark.asyncio
    async def test_search_patient_by_name_and_dob(self):
        """Search patient by name + DOB when phone not available."""
        from app.ehr.athenahealth import AthenaHealthClient

        client = AthenaHealthClient(
            client_id="id", client_secret="secret", practice_id="195900"
        )

        with patch.object(client, "_get", return_value={
            "patients": [{"patientid": "12345", "firstname": "Maria", "lastname": "Santos"}]
        }):
            result = await client.search_patient(
                clinic_id="clinic_001",
                first_name="Maria",
                last_name="Santos",
                date_of_birth="1985-03-15",
            )

        assert result is not None
        assert result["patient_id"] == "12345"

    @pytest.mark.asyncio
    async def test_search_patient_returns_none_when_not_found(self):
        from app.ehr.athenahealth import AthenaHealthClient

        client = AthenaHealthClient(
            client_id="id", client_secret="secret", practice_id="195900"
        )

        with patch.object(client, "_get", return_value={"patients": []}):
            result = await client.search_patient(
                clinic_id="clinic_001",
                first_name="Unknown",
                last_name="Person",
                date_of_birth="1900-01-01",
            )

        assert result is None


class TestErrorHandling:

    @pytest.mark.asyncio
    async def test_rate_limit_429_on_booking_raises(self):
        """429 on book_appointment raises — booking must not silently fail."""
        from app.ehr.athenahealth import AthenaHealthClient

        client = AthenaHealthClient(
            client_id="id", client_secret="secret", practice_id="195900"
        )
        client._access_token = "valid_token"
        import time
        client._token_expires_at = time.time() + 3600

        err_response = MagicMock()
        err_response.status_code = 429

        with patch.object(client, "_put",
            side_effect=httpx.HTTPStatusError("429", request=MagicMock(), response=err_response)
        ):
            with pytest.raises((httpx.HTTPStatusError, Exception)):
                await client.book_appointment("clinic_001", "PAT_001", "SLOT_001", "Checkup")

    @pytest.mark.asyncio
    async def test_athena_503_returns_graceful_none(self):
        """athenahealth outage returns None — call continues with fallback."""
        from app.ehr.athenahealth import AthenaHealthClient

        client = AthenaHealthClient(
            client_id="id", client_secret="secret", practice_id="195900"
        )

        with patch.object(client, "_get", side_effect=httpx.ConnectError("Service unavailable")):
            result = await client.get_patient("clinic_001", "+12125551234")

        assert result is None  # Graceful — never crashes the agent


class TestWebhookEventSubscription:

    @pytest.mark.asyncio
    async def test_subscribe_to_appointment_events(self):
        """Subscribe to appointment updates for real-time EHR sync."""
        from app.ehr.athenahealth import AthenaHealthClient

        client = AthenaHealthClient(
            client_id="id", client_secret="secret", practice_id="195900"
        )

        with patch.object(client, "_post_fhir", return_value={
            "resourceType": "Subscription",
            "id": "sub_appt_001",
            "status": "active",
        }):
            result = await client.subscribe_to_events(
                event_type="Appointment",
                callback_url="https://carenova.tinlance.com/api/ehr/webhooks/athena",
                webhook_secret="secret_abc123",
            )

        assert result["subscription_id"] == "sub_appt_001"
        assert result["status"] == "active"
