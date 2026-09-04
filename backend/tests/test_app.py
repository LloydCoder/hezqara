"""Application boundary and repository contract tests."""
from pathlib import Path

from fastapi.testclient import TestClient


ROOT = Path(__file__).resolve().parents[2]
MIGRATIONS = ROOT / "supabase" / "migrations"


def test_settings_can_be_imported():
    from app.config import Settings
    assert Settings is not None


def test_settings_has_expected_app_port():
    from app.config import settings
    assert settings.app_port == 8004


def test_settings_has_lemonsqueezy_store_id():
    from app.config import settings
    assert settings.lemonsqueezy_store_id == "247127"


def test_bridge_urls_do_not_have_hardcoded_private_ips():
    from app.config import settings
    for name in ("fusionops_url", "ai_shield_url", "threatfade_url", "resilientai_url"):
        assert "13.50.16.19" not in getattr(settings, name)


def test_app_can_be_imported():
    from app.main import app
    assert app is not None


def test_app_identity():
    from app.main import app
    assert app.title == "HEZQARA AI"


def test_health_endpoint_returns_200():
    from app.main import app
    response = TestClient(app).get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["service"] == "hezqara-ai"
    assert response.json()["port"] == 8004


def test_root_endpoint_returns_200():
    from app.main import app
    response = TestClient(app).get("/")
    assert response.status_code == 200


def test_voice_webhook_endpoint_exists():
    from app.main import app
    response = TestClient(app).post(
        "/voice/webhook",
        json={"event": "ping"},
        headers={"x-retell-signature": "skip_for_test"},
    )
    assert response.status_code != 404


def test_openapi_schema_accessible_in_dev():
    from app.main import app
    response = TestClient(app).get("/docs")
    assert response.status_code == 200


def test_migrations_exist_and_are_sequential():
    files = sorted(p.name for p in MIGRATIONS.glob("*.sql"))
    assert len(files) >= 12
    for index, name in enumerate(files, 1):
        assert name.startswith(f"{index:03d}_"), name
    assert "011_create_audit_log.sql" in files
    assert "012_enable_rls.sql" in files
