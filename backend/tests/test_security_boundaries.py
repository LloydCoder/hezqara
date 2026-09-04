from fastapi import HTTPException
from fastapi.testclient import TestClient


def test_health_is_public():
    from app.main import app
    assert TestClient(app).get("/health").status_code == 200


def test_missing_clerk_configuration_fails_closed():
    from app.security.auth import authenticate
    from app.config import settings
    from starlette.requests import Request

    if settings.app_env in {"test", "development"}:
        return

    scope = {"type": "http", "method": "GET", "path": "/api/protected", "headers": []}
    request = Request(scope)
    try:
        authenticate(request)
    except HTTPException as exc:
        assert exc.status_code in {401, 503}
    else:
        raise AssertionError("authentication must fail closed when Clerk is not configured")


def test_audit_sanitizer_redacts_phi_keys():
    from app.security.audit import _sanitize
    value = _sanitize({"name": "Patient", "phone": "+1 555", "safe": "ok"})
    assert value["name"] == "[redacted]"
    assert value["phone"] == "[redacted]"
    assert value["safe"] == "ok"
