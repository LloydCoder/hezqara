from app.integrations.core.smart import (
    SMARTConfiguration,
    SMARTValidationError,
    build_authorization_url,
    create_oauth_state,
    create_pkce,
    validate_token_response,
)
from app.integrations.fhir.adapter import FHIRAdapter, FHIRValidationError
from app.integrations.fhir.standards import (
    DAVINCI_IMPLEMENTATION_GUIDES,
    FHIR_R4_VERSION,
    SMART_APP_LAUNCH_VERSION,
)


def test_smart_discovery_and_pkce_are_secure():
    config = SMARTConfiguration.from_document(
        {
            "issuer": "https://ehr.example.com",
            "authorization_endpoint": "https://ehr.example.com/auth",
            "token_endpoint": "https://ehr.example.com/token",
            "jwks_uri": "https://ehr.example.com/jwks",
            "scopes_supported": [
                "openid",
                "fhirUser",
                "launch",
                "launch/patient",
                "patient/Patient.rs",
            ],
        }
    )
    pkce = create_pkce()
    state = create_oauth_state()
    url = build_authorization_url(
        config,
        "hezqara-client",
        "https://hezqara.example/callback",
        ["openid", "fhirUser", "patient/Patient.rs"],
        state,
        pkce,
        {"patient": "123"},
        "nonce",
    )
    assert "code_challenge_method=S256" in url
    assert "launch%2Fpatient" in url
    assert state in url
    assert pkce.challenge in url


def test_smart_rejects_unsupported_scope_and_insecure_endpoints():
    config = SMARTConfiguration.from_document(
        {
            "issuer": "https://ehr.example.com",
            "authorization_endpoint": "https://ehr.example.com/auth",
            "token_endpoint": "https://ehr.example.com/token",
            "scopes_supported": ["openid"],
        }
    )
    try:
        build_authorization_url(
            config,
            "client",
            "https://app.example/cb",
            ["patient/*.rs"],
            create_oauth_state(),
            create_pkce(),
        )
    except SMARTValidationError:
        pass
    else:
        raise AssertionError("unsupported scope accepted")

    try:
        SMARTConfiguration.from_document(
            {
                "issuer": "http://ehr.example.com",
                "authorization_endpoint": "https://ehr.example.com/auth",
                "token_endpoint": "https://ehr.example.com/token",
            }
        )
    except SMARTValidationError:
        pass
    else:
        raise AssertionError("insecure SMART issuer accepted")


def test_smart_requires_nonce_for_openid_and_s256_pkce():
    config = SMARTConfiguration.from_document(
        {
            "issuer": "https://ehr.example.com",
            "authorization_endpoint": "https://ehr.example.com/auth",
            "token_endpoint": "https://ehr.example.com/token",
            "scopes_supported": ["openid"],
        }
    )
    try:
        build_authorization_url(
            config,
            "client",
            "https://app.example/cb",
            ["openid"],
            create_oauth_state(),
            create_pkce(),
        )
    except SMARTValidationError:
        pass
    else:
        raise AssertionError("openid flow accepted without nonce")

    try:
        build_authorization_url(
            config,
            "client",
            "http://app.example/cb",
            ["openid"],
            create_oauth_state(),
            create_pkce(),
            nonce="nonce",
        )
    except SMARTValidationError:
        pass
    else:
        raise AssertionError("insecure redirect URI accepted")


def test_token_metadata_does_not_return_raw_tokens():
    result = validate_token_response(
        {
            "access_token": "secret",
            "refresh_token": "refresh-secret",
            "token_type": "Bearer",
            "scope": "patient/Patient.rs patient/Patient.rs",
            "expires_in": 300,
        }
    )
    assert result["token_type"] == "Bearer"
    assert result["scope"] == ("patient/Patient.rs",)
    assert result["expires_in"] == 300
    assert result["refresh_token_present"] is True
    assert "access_token" not in result
    assert "refresh_token" not in result


def test_token_metadata_rejects_invalid_expiry():
    try:
        validate_token_response({"access_token": "secret", "expires_in": 0})
    except SMARTValidationError:
        pass
    else:
        raise AssertionError("invalid token expiry accepted")


def test_fhir_bundle_and_operation_outcome_validation():
    assert FHIRAdapter.bundle(
        {"resourceType": "Bundle", "type": "searchset", "entry": []}
    ).resource_type == "Bundle"
    assert FHIRAdapter.operation_outcome(
        {"resourceType": "OperationOutcome", "issue": [{"severity": "error", "code": "invalid"}]}
    ).resource_type == "OperationOutcome"
    try:
        FHIRAdapter.bundle({"resourceType": "Bundle"})
    except FHIRValidationError:
        pass
    else:
        raise AssertionError("invalid Bundle accepted")


def test_current_interoperability_contract_versions():
    assert FHIR_R4_VERSION == "4.0.1"
    assert SMART_APP_LAUNCH_VERSION == "2.2.0"
    assert DAVINCI_IMPLEMENTATION_GUIDES["CRD"] == "2.2.1"
    assert DAVINCI_IMPLEMENTATION_GUIDES["PAS"] == "2.2.1"
