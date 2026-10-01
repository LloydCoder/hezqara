import subprocess
import sys
import time

import httpx
from app.tasks.celery import celery_app

BASE = "http://127.0.0.1:8004"


def call(client, method, path, **kwargs):
    response = client.request(
        method,
        path,
        timeout=15,
        headers={"x-test-auth": "1", **kwargs.pop("headers", {})},
        **kwargs,
    )
    print(f"{method} {path} -> {response.status_code} {response.text}", flush=True)
    response.raise_for_status()
    return response.json()


worker = subprocess.Popen(
    [
        sys.executable, "-m", "celery", "-A", "app.tasks.celery", "worker",
        "--loglevel=warning", "--pool=solo", "--concurrency=1",
        "--without-gossip", "--without-mingle", "--hostname", "e7@%h", "-Q", "hezqara",
    ],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
)

proc = subprocess.Popen(
    [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8004"],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
)
try:
    with httpx.Client(base_url=BASE) as client:
        for _ in range(30):
            try:
                if client.get("/health", timeout=2).is_success:
                    break
            except httpx.HTTPError:
                pass
            time.sleep(1)

        call(client, "GET", "/health")
        for _ in range(30):
            if worker.poll() is not None:
                raise AssertionError("Celery worker exited before the workflow slice started")
            try:
                inspector = celery_app.control.inspect(timeout=1)
                if inspector.ping():
                    registered = inspector.registered() or {}
                    queues = inspector.active_queues() or {}
                    tasks = next(iter(registered.values()), [])
                    active = next(iter(queues.values()), [])
                    queue_names = {item.get("name") for item in active}
                    if "app.tasks.durable.run_platform_job" in tasks and "hezqara" in queue_names:
                        print(f"Celery worker ready: tasks={len(tasks)} queues={sorted(queue_names)}", flush=True)
                        break
                    raise AssertionError(f"Celery worker is ready but durable task is not registered: {tasks}")
            except Exception:
                pass
            time.sleep(1)
        else:
            raise AssertionError("Celery worker did not become ready")

        for step in ("clinic_profile", "users", "ai_controls", "communications", "billing", "first_workflow"):
            call(client, "POST", "/api/v1/platform/onboarding/complete", json={"step": step})

        call(client, "POST", "/api/v1/platform/subscription/plan", json={"plan_code": "starter"})

        integration = call(
            client,
            "POST",
            "/api/v1/integrations",
            json={
                "name": "CI FHIR",
                "category": "ehr",
                "provider_key": "test-fhir",
                "api_version": "R4",
                "environment": "test",
            },
        )
        call(client, "POST", f"/api/v1/integrations/{integration['id']}/test-connection")
        call(client, "POST", f"/api/v1/integrations/{integration['id']}/activate")

        workflow = call(
            client,
            "POST",
            "/api/v1/workflows",
            json={
                "key": "e7_first_clinic",
                "name": "E7 First Clinic Workflow",
                "definition": {
                    "steps": [
                        {
                            "key": "approval",
                            "type": "request_approval",
                            "input": {
                                "risk_level": "EXTERNAL_SIDE_EFFECT",
                                "action": {"type": "send_patient_message"},
                            },
                        },
                        {"key": "finish", "type": "complete"},
                    ]
                },
            },
        )
        workflow_id = workflow["id"]
        call(client, "POST", f"/api/v1/workflows/{workflow_id}/activate")

        preflight = call(client, "POST", "/api/v1/platform/activation/preflight")
        assert preflight["ready"], preflight

        activated = call(client, "POST", "/api/v1/platform/activation/activate")
        assert activated["state"] == "active", activated

        run = call(
            client,
            "POST",
            f"/api/v1/workflows/{workflow_id}/runs",
            json={
                "idempotency_key": "e7-first-clinic-work-001",
                "trigger_type": "manual",
                "context": {"vertical_slice": "e7"},
            },
        )
        for _ in range(60):
            if run["status"] == "waiting_for_approval":
                break
            if run["status"] in {"failed", "escalated", "cancelled"}:
                break
            time.sleep(1)
            run = call(client, "GET", f"/api/v1/workflows/{workflow_id}/runs")[0]
        assert run["status"] == "waiting_for_approval", run

        approvals = call(client, "GET", "/api/v1/approvals")
        approval = next(item for item in approvals if item["workflow_run_id"] == run["id"])
        call(client, "POST", f"/api/v1/approvals/{approval['id']}/approve")

        for _ in range(60):
            runs = call(client, "GET", f"/api/v1/workflows/{workflow_id}/runs")
            if runs[0]["status"] == "completed":
                break
            if runs[0]["status"] in {"failed", "escalated", "cancelled"}:
                break
            time.sleep(1)
        assert runs[0]["status"] == "completed", runs

        roi = call(client, "POST", "/api/v1/platform/activation/roi")
        assert roi["completed_workflows"] >= 1, roi

        export_manifest = call(client, "POST", "/api/v1/platform/activation/export")
        assert export_manifest["status"] == "ready", export_manifest
        assert export_manifest["record_counts"]["workflow_runs"] >= 1, export_manifest

        paused = call(client, "POST", "/api/v1/platform/activation/pause", json={"reason": "CI pause"})
        assert paused["state"] == "paused", paused

        disabled = call(client, "POST", "/api/v1/platform/activation/disable", json={"reason": "CI disable"})
        assert disabled["state"] == "disabled", disabled

        recovered = call(client, "POST", "/api/v1/platform/activation/recover", json={"reason": "CI recovery"})
        assert recovered["state"] == "recovered", recovered

        rolled_back = call(client, "POST", "/api/v1/platform/activation/rollback", json={"reason": "CI rollback"})
        assert rolled_back["state"] == "disabled", rolled_back

        recovered_again = call(client, "POST", "/api/v1/platform/activation/recover", json={"reason": "CI recovery after rollback"})
        assert recovered_again["state"] == "recovered", recovered_again

        active_again = call(client, "POST", "/api/v1/platform/activation/activate")
        assert active_again["state"] == "active", active_again

        final_state = call(client, "GET", "/api/v1/platform/activation")
        assert final_state["state"] == "active", final_state
finally:
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
    for child, name in ((proc, "uvicorn"), (worker, "celery")):
        if child.poll() is None:
            child.terminate()
            try:
                child.wait(timeout=5)
            except subprocess.TimeoutExpired:
                child.kill()
        output = child.stdout.read() if child.stdout else ""
        if output:
            print(f"--- {name} output ---", flush=True)
            print(output, flush=True)
