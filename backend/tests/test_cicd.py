"""
CI/CD Pipeline Tests — Sprint 21
Validates GitHub Actions workflows and deployment config.
"""
import os
import pytest
import yaml

GITHUB_DIR = "../../.github"
WORKFLOWS_DIR = f"{GITHUB_DIR}/workflows"


class TestGitHubWorkflows:

    def test_ci_workflow_exists(self):
        assert os.path.exists(f"{WORKFLOWS_DIR}/ci.yml")

    def test_deploy_workflow_exists(self):
        assert os.path.exists(f"{WORKFLOWS_DIR}/deploy.yml")

    def test_security_scan_workflow_exists(self):
        assert os.path.exists(f"{WORKFLOWS_DIR}/security-scan.yml")

    def test_pr_template_exists(self):
        assert os.path.exists(f"{GITHUB_DIR}/PULL_REQUEST_TEMPLATE.md")

    def test_ci_workflow_valid_yaml(self):
        with open(f"{WORKFLOWS_DIR}/ci.yml") as f:
            data = yaml.safe_load(f)
        assert data is not None
        assert "jobs" in data

    def test_deploy_workflow_valid_yaml(self):
        with open(f"{WORKFLOWS_DIR}/deploy.yml") as f:
            data = yaml.safe_load(f)
        assert data is not None
        assert "jobs" in data

    def test_security_workflow_valid_yaml(self):
        with open(f"{WORKFLOWS_DIR}/security-scan.yml") as f:
            data = yaml.safe_load(f)
        assert data is not None


class TestCIWorkflowContent:

    def test_ci_triggers_on_pull_request(self):
        with open(f"{WORKFLOWS_DIR}/ci.yml") as f:
            data = yaml.safe_load(f)
        assert "pull_request" in data.get(True, {})

    def test_ci_triggers_on_push_to_main(self):
        with open(f"{WORKFLOWS_DIR}/ci.yml") as f:
            data = yaml.safe_load(f)
        on = data.get(True, {})
        push = on.get("push", {})
        assert "main" in push.get("branches", [])

    def test_ci_has_backend_test_job(self):
        with open(f"{WORKFLOWS_DIR}/ci.yml") as f:
            data = yaml.safe_load(f)
        assert "backend-test" in data["jobs"]

    def test_ci_has_security_scan_job(self):
        with open(f"{WORKFLOWS_DIR}/ci.yml") as f:
            data = yaml.safe_load(f)
        assert "security-scan" in data["jobs"]

    def test_ci_has_frontend_check_job(self):
        with open(f"{WORKFLOWS_DIR}/ci.yml") as f:
            data = yaml.safe_load(f)
        assert "frontend-check" in data["jobs"]

    def test_ci_has_docker_build_job(self):
        with open(f"{WORKFLOWS_DIR}/ci.yml") as f:
            data = yaml.safe_load(f)
        assert "docker-build" in data["jobs"]

    def test_ci_backend_uses_python_312(self):
        with open(f"{WORKFLOWS_DIR}/ci.yml") as f:
            data = yaml.safe_load(f)
        job = data["jobs"]["backend-test"]
        steps = job.get("steps", [])
        python_step = next(
            (s for s in steps if "python-version" in str(s.get("with", {}))), None
        )
        assert python_step is not None
        assert "3.12" in str(python_step["with"]["python-version"])

    def test_ci_uses_trufflehog(self):
        with open(f"{WORKFLOWS_DIR}/ci.yml") as f:
            content = f.read()
        assert "trufflehog" in content.lower()

    def test_ci_has_coverage_requirement(self):
        """Tests must maintain ≥80% coverage."""
        with open(f"{WORKFLOWS_DIR}/ci.yml") as f:
            content = f.read()
        assert "cov-fail-under=80" in content


class TestDeployWorkflowContent:

    def test_deploy_only_on_main(self):
        with open(f"{WORKFLOWS_DIR}/deploy.yml") as f:
            data = yaml.safe_load(f)
        on = data.get(True, {})
        push = on.get("push", {})
        branches = push.get("branches", [])
        assert branches == ["main"]

    def test_deploy_targets_correct_ec2_ip(self):
        with open(f"{WORKFLOWS_DIR}/deploy.yml") as f:
            content = f.read()
        assert "13.50.16.19" in content

    def test_deploy_has_health_check_verification(self):
        with open(f"{WORKFLOWS_DIR}/deploy.yml") as f:
            content = f.read()
        assert "/health" in content

    def test_deploy_uses_concurrency_single_deploy(self):
        """Only one deploy at a time — no parallel deploys."""
        with open(f"{WORKFLOWS_DIR}/deploy.yml") as f:
            data = yaml.safe_load(f)
        assert "concurrency" in data
        assert data["concurrency"].get("cancel-in-progress") is False

    def test_deploy_notifies_fusionops(self):
        """Deploy events reach FusionOps hub."""
        with open(f"{WORKFLOWS_DIR}/deploy.yml") as f:
            content = f.read()
        assert "FUSIONOPS" in content

    def test_deploy_has_environment_protection(self):
        """Production environment requires manual approval."""
        with open(f"{WORKFLOWS_DIR}/deploy.yml") as f:
            data = yaml.safe_load(f)
        job = data["jobs"]["deploy"]
        assert job.get("environment") == "production"


class TestSecurityWorkflow:

    def test_security_scan_runs_on_schedule(self):
        """Daily security scans even without PRs."""
        with open(f"{WORKFLOWS_DIR}/security-scan.yml") as f:
            data = yaml.safe_load(f)
        on = data.get(True, {})
        assert "schedule" in on

    def test_security_scan_checks_for_phi(self):
        with open(f"{WORKFLOWS_DIR}/security-scan.yml") as f:
            content = f.read()
        assert "PHI" in content or "phi" in content.lower()

    def test_security_scan_checks_for_env_files(self):
        with open(f"{WORKFLOWS_DIR}/security-scan.yml") as f:
            content = f.read()
        assert ".env" in content


class TestGitignore:

    def test_gitignore_exists(self):
        assert os.path.exists("../../.gitignore")

    def test_gitignore_excludes_env_files(self):
        with open("../../.gitignore") as f:
            content = f.read()
        assert ".env" in content

    def test_gitignore_keeps_env_example(self):
        with open("../../.gitignore") as f:
            content = f.read()
        assert "!.env.example" in content

    def test_gitignore_excludes_pycache(self):
        with open("../../.gitignore") as f:
            content = f.read()
        assert "__pycache__" in content

    def test_gitignore_excludes_node_modules(self):
        with open("../../.gitignore") as f:
            content = f.read()
        assert "node_modules" in content

    def test_gitignore_excludes_next_build(self):
        with open("../../.gitignore") as f:
            content = f.read()
        assert ".next/" in content

    def test_gitignore_excludes_secrets(self):
        with open("../../.gitignore") as f:
            content = f.read()
        assert "*.pem" in content
        assert "*.key" in content
