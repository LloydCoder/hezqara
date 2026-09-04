"""
Infrastructure + Deployment Tests — Sprint 20
Validates Docker config, nginx config, systemd unit,
scripts, and .env completeness.
"""
import os
import pytest


INFRA_DIR = "../../infrastructure"
BACKEND_DIR = "../../backend"
FRONTEND_DIR = "../../frontend"


class TestDockerfiles:

    def test_backend_dockerfile_exists(self):
        assert os.path.exists(f"{BACKEND_DIR}/Dockerfile")

    def test_frontend_dockerfile_exists(self):
        assert os.path.exists(f"{FRONTEND_DIR}/Dockerfile")

    def test_backend_dockerfile_has_healthcheck(self):
        with open(f"{BACKEND_DIR}/Dockerfile") as f:
            content = f.read()
        assert "HEALTHCHECK" in content

    def test_backend_dockerfile_uses_port_8004(self):
        with open(f"{BACKEND_DIR}/Dockerfile") as f:
            content = f.read()
        assert "8004" in content

    def test_backend_dockerfile_runs_as_non_root(self):
        """Security: never run as root in production."""
        with open(f"{BACKEND_DIR}/Dockerfile") as f:
            content = f.read()
        assert "USER carenova" in content

    def test_backend_dockerfile_has_multistage_build(self):
        """Multi-stage build keeps image size small."""
        with open(f"{BACKEND_DIR}/Dockerfile") as f:
            content = f.read()
        assert content.count("FROM") >= 2


class TestDockerCompose:

    def test_docker_compose_exists(self):
        assert os.path.exists(f"{INFRA_DIR}/docker/docker-compose.yml")

    def test_docker_compose_prod_exists(self):
        assert os.path.exists(f"{INFRA_DIR}/docker/docker-compose.prod.yml")

    def test_docker_compose_has_backend_service(self):
        with open(f"{INFRA_DIR}/docker/docker-compose.yml") as f:
            content = f.read()
        assert "backend:" in content

    def test_docker_compose_has_celery_worker(self):
        with open(f"{INFRA_DIR}/docker/docker-compose.yml") as f:
            content = f.read()
        assert "celery-worker:" in content

    def test_docker_compose_has_celery_beat(self):
        with open(f"{INFRA_DIR}/docker/docker-compose.yml") as f:
            content = f.read()
        assert "celery-beat:" in content

    def test_docker_compose_has_redis(self):
        with open(f"{INFRA_DIR}/docker/docker-compose.yml") as f:
            content = f.read()
        assert "redis:" in content

    def test_docker_compose_has_falkordb(self):
        with open(f"{INFRA_DIR}/docker/docker-compose.yml") as f:
            content = f.read()
        assert "falkordb:" in content

    def test_docker_compose_has_graphiti(self):
        with open(f"{INFRA_DIR}/docker/docker-compose.yml") as f:
            content = f.read()
        assert "graphiti:" in content

    def test_docker_compose_backend_port_8004(self):
        with open(f"{INFRA_DIR}/docker/docker-compose.yml") as f:
            content = f.read()
        assert "8004" in content

    def test_prod_compose_disables_volume_mounts(self):
        """Production must not mount source code — security risk."""
        with open(f"{INFRA_DIR}/docker/docker-compose.prod.yml") as f:
            content = f.read()
        assert "volumes: []" in content


class TestNginxConfig:

    def test_nginx_config_exists(self):
        assert os.path.exists(f"{INFRA_DIR}/docker/nginx/carenova.conf")

    def test_nginx_targets_correct_domain(self):
        with open(f"{INFRA_DIR}/docker/nginx/carenova.conf") as f:
            content = f.read()
        assert "carenova.tinlance.com" in content

    def test_nginx_proxies_to_port_8004(self):
        with open(f"{INFRA_DIR}/docker/nginx/carenova.conf") as f:
            content = f.read()
        assert "8004" in content

    def test_nginx_has_ssl_config(self):
        with open(f"{INFRA_DIR}/docker/nginx/carenova.conf") as f:
            content = f.read()
        assert "ssl_certificate" in content
        assert "TLSv1.3" in content

    def test_nginx_redirects_http_to_https(self):
        with open(f"{INFRA_DIR}/docker/nginx/carenova.conf") as f:
            content = f.read()
        assert "return 301 https://" in content

    def test_nginx_has_hsts_header(self):
        """HIPAA requires HSTS for all web traffic."""
        with open(f"{INFRA_DIR}/docker/nginx/carenova.conf") as f:
            content = f.read()
        assert "Strict-Transport-Security" in content

    def test_nginx_has_rate_limiting(self):
        with open(f"{INFRA_DIR}/docker/nginx/carenova.conf") as f:
            content = f.read()
        assert "limit_req_zone" in content

    def test_nginx_blocks_api_docs_in_prod(self):
        """API docs must be blocked in production — OWASP."""
        with open(f"{INFRA_DIR}/docker/nginx/carenova.conf") as f:
            content = f.read()
        assert "/docs" in content
        assert "deny all" in content

    def test_nginx_has_webhook_route(self):
        with open(f"{INFRA_DIR}/docker/nginx/carenova.conf") as f:
            content = f.read()
        assert "voice/webhook" in content

    def test_nginx_has_extended_timeout_for_webhooks(self):
        """Retell webhooks can take time — need extended timeout."""
        with open(f"{INFRA_DIR}/docker/nginx/carenova.conf") as f:
            content = f.read()
        assert "proxy_read_timeout 300s" in content


class TestSystemdService:

    def test_systemd_service_exists(self):
        assert os.path.exists(f"{INFRA_DIR}/systemd/carenova.service")

    def test_systemd_service_has_correct_description(self):
        with open(f"{INFRA_DIR}/systemd/carenova.service") as f:
            content = f.read()
        assert "Carenova AI" in content

    def test_systemd_service_requires_docker(self):
        with open(f"{INFRA_DIR}/systemd/carenova.service") as f:
            content = f.read()
        assert "docker.service" in content

    def test_systemd_service_has_restart_policy(self):
        with open(f"{INFRA_DIR}/systemd/carenova.service") as f:
            content = f.read()
        assert "Restart=" in content

    def test_systemd_service_uses_environment_file(self):
        with open(f"{INFRA_DIR}/systemd/carenova.service") as f:
            content = f.read()
        assert "EnvironmentFile=" in content

    def test_systemd_service_enabled_at_boot(self):
        with open(f"{INFRA_DIR}/systemd/carenova.service") as f:
            content = f.read()
        assert "WantedBy=multi-user.target" in content


class TestDeployScripts:

    def test_setup_ec2_script_exists(self):
        assert os.path.exists(f"{INFRA_DIR}/scripts/setup_ec2.sh")

    def test_deploy_script_exists(self):
        assert os.path.exists(f"{INFRA_DIR}/scripts/deploy.sh")

    def test_backup_script_exists(self):
        assert os.path.exists(f"{INFRA_DIR}/scripts/backup_db.sh")

    def test_scripts_are_executable(self):
        for script in ["setup_ec2.sh", "deploy.sh", "backup_db.sh"]:
            path = f"{INFRA_DIR}/scripts/{script}"
            assert os.access(path, os.X_OK), f"{script} not executable"

    def test_deploy_script_has_health_check(self):
        with open(f"{INFRA_DIR}/scripts/deploy.sh") as f:
            content = f.read()
        assert "/health" in content

    def test_deploy_script_has_rollback(self):
        with open(f"{INFRA_DIR}/scripts/deploy.sh") as f:
            content = f.read()
        assert "Rolling back" in content or "rollback" in content.lower()

    def test_setup_script_targets_correct_ec2_ip(self):
        with open(f"{INFRA_DIR}/scripts/setup_ec2.sh") as f:
            content = f.read()
        assert "13.50.16.19" in content

    def test_setup_script_configures_firewall(self):
        with open(f"{INFRA_DIR}/scripts/setup_ec2.sh") as f:
            content = f.read()
        assert "ufw" in content
        assert "8004" in content


class TestEnvExample:

    def test_env_example_exists(self):
        assert os.path.exists(f"{BACKEND_DIR}/.env.example")

    def test_env_example_has_stripe_keys(self):
        with open(f"{BACKEND_DIR}/.env.example") as f:
            content = f.read()
        assert "STRIPE_SECRET_KEY" in content

    def test_env_example_has_retell_keys(self):
        with open(f"{BACKEND_DIR}/.env.example") as f:
            content = f.read()
        assert "RETELL_API_KEY" in content

    def test_env_example_has_lemonsqueezy_store_id(self):
        with open(f"{BACKEND_DIR}/.env.example") as f:
            content = f.read()
        assert "247127" in content

    def test_env_example_has_ec2_bridge_urls(self):
        with open(f"{BACKEND_DIR}/.env.example") as f:
            content = f.read()
        assert "13.50.16.19" in content

    def test_env_example_has_all_required_sections(self):
        with open(f"{BACKEND_DIR}/.env.example") as f:
            content = f.read()
        required = [
            "APP_ENV",
            "DATABASE_URL",
            "CLERK_SECRET_KEY",
            "LEMONSQUEEZY_API_KEY",
            "PAYSTACK_SECRET_KEY",
            "STRIPE_SECRET_KEY",
            "RESEND_API_KEY",
            "RETELL_API_KEY",
            "ANTHROPIC_API_KEY",
            "FUSIONOPS_URL",
            "AI_SHIELD_URL",
            "GRAPHITI_URL",
        ]
        for key in required:
            assert key in content, f"Missing from .env.example: {key}"
