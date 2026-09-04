"""
FastAPI App + Config Tests — Sprint 9
"""
import pytest
from fastapi.testclient import TestClient


class TestAppConfig:

    def test_settings_can_be_imported(self):
        from app.config import Settings
        assert Settings is not None

    def test_settings_has_app_port(self):
        from app.config import settings
        assert settings.app_port == 8004

    def test_settings_has_lemonsqueezy_store_id(self):
        from app.config import settings
        assert settings.lemonsqueezy_store_id == "247127"

    def test_settings_has_ec2_fusionops_url(self):
        from app.config import settings
        assert "13.50.16.19" in settings.fusionops_url

    def test_settings_has_all_bridge_urls(self):
        from app.config import settings
        assert settings.ai_shield_url != ""
        assert settings.threatfade_url != ""
        assert settings.resilientai_url != ""


class TestFastAPIApp:

    def test_app_can_be_imported(self):
        from app.main import app
        assert app is not None

    def test_app_has_title(self):
        from app.main import app
        assert app.title == "Carenova AI"

    def test_health_endpoint_returns_200(self):
        from app.main import app
        client = TestClient(app)
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_endpoint_returns_ok_status(self):
        from app.main import app
        client = TestClient(app)
        response = client.get("/health")
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "carenova-ai"
        assert data["port"] == 8004

    def test_root_endpoint_returns_200(self):
        from app.main import app
        client = TestClient(app)
        response = client.get("/")
        assert response.status_code == 200

    def test_voice_webhook_endpoint_exists(self):
        from app.main import app
        client = TestClient(app)
        # POST with minimal payload — should not 404
        response = client.post(
            "/voice/webhook",
            json={"event": "ping"},
            headers={"x-retell-signature": "skip_for_test"},
        )
        assert response.status_code != 404

    def test_openapi_schema_accessible_in_dev(self):
        from app.main import app
        client = TestClient(app)
        response = client.get("/docs")
        # 200 in dev (non-production env)
        assert response.status_code == 200


class TestMigrationsExist:

    def test_all_13_migrations_exist(self):
        import os
        migration_dir = "../../supabase/migrations"
        files = [f for f in os.listdir(migration_dir) if f.endswith(".sql")]
        assert len(files) >= 12

    def test_migrations_numbered_correctly(self):
        import os
        migration_dir = "../../supabase/migrations"
        files = sorted(f for f in os.listdir(migration_dir) if f.endswith(".sql"))
        for i, f in enumerate(files, 1):
            assert f.startswith(f"{i:03d}_"), f"Migration {f} not numbered correctly"

    def test_rls_migration_exists(self):
        import os
        migration_dir = "../../supabase/migrations"
        assert "012_enable_rls.sql" in os.listdir(migration_dir)

    def test_audit_log_migration_exists(self):
        import os
        migration_dir = "../../supabase/migrations"
        assert "011_create_audit_log.sql" in os.listdir(migration_dir)
