import json
from uuid import uuid4

import httpx
import pytest

from app import main as app_main
from app.api.routes import demo as demo_route
from app.core.config import Settings
from app.schemas.chat import ChatResponse


IDENTITY_TOKEN = "private-synthetic-test-token"
WORKSPACE_PUBLIC_ID = str(uuid4())
WORKSPACE_ID = str(uuid4())
CUSTOMER_ID = str(uuid4())
RUN_ID = str(uuid4())


def _write_config(path, **overrides):
    config = {
        "workspace_public_id": WORKSPACE_PUBLIC_ID,
        "workspace_id": WORKSPACE_ID,
        "customer_id": CUSTOMER_ID,
        "identity_token": IDENTITY_TOKEN,
        "demo_namespace": demo_route.EXPECTED_DEMO_NAMESPACE,
        "synthetic_data": True,
    }
    config.update(overrides)
    path.write_text(json.dumps(config), encoding="utf-8")
    path.with_name(f"{path.name}.run.json").write_text(json.dumps({
        "customer_id": config["customer_id"],
        "active_run_id": None,
    }), encoding="utf-8")
    return config


class FakeWorkflow:
    def __init__(self, *, partial=False):
        self.calls = []
        self.partial = partial

    async def handle(self, **kwargs):
        self.calls.append(kwargs)
        response = kwargs["http_response"]
        response.headers["X-Workflow-Status"] = "complete"
        response.headers["X-Memory-Status"] = "stored"
        if self.partial:
            response.status_code = 202
            response.headers["X-Workflow-Status"] = "escalation-pending"
        return ChatResponse(
            response="A synthetic support response.",
            session_id=kwargs["request"].session_id,
            sentiment="neutral",
            memories_used=["memory-1"],
            memory_retrieved=True,
            escalation_required=self.partial,
            escalation_reason="Human follow-up recommended." if self.partial else None,
        )


def _app(monkeypatch, *, app_env="development", enabled=True, workflow=None):
    settings = Settings(
        app_env=app_env,
        allow_synthetic_demo_seed=enabled,
        _env_file=None,
    )
    monkeypatch.setattr(app_main, "get_settings", lambda: settings)
    application = app_main.create_app()
    application.state.settings = settings
    application.state.chat_workflow = workflow or FakeWorkflow()
    return application


async def _post(application, *, body=None, key="dashboard-demo-key-001"):
    transport = httpx.ASGITransport(app=application)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        headers = {} if key is None else {"Idempotency-Key": key}
        return await client.post("/api/v1/demo/chat", headers=headers, json=body or {
            "session_id": f"sarah-dashboard-{RUN_ID}-learning",
            "message": "My headphones continue disconnecting.",
        })


@pytest.mark.asyncio
async def test_dashboard_demo_development_opt_in_delegates_server_identity_and_preserves_headers(
    monkeypatch, tmp_path,
):
    config_path = tmp_path / ".sarah_dashboard_demo.json"
    _write_config(config_path)
    monkeypatch.setattr(demo_route, "DASHBOARD_DEMO_CONFIG_PATH", config_path)
    workflow = FakeWorkflow(partial=True)
    application = _app(monkeypatch, workflow=workflow)

    response = await _post(application)

    assert response.status_code == 202
    assert response.headers["X-Workflow-Status"] == "escalation-pending"
    assert response.headers["X-Memory-Status"] == "stored"
    assert response.json()["session_id"] == f"sarah-dashboard-{RUN_ID}-learning"
    assert set(response.json()) == {
        "response", "session_id", "sentiment", "memories_used", "memory_retrieved",
        "escalation_required", "escalation_reason",
    }
    assert "identity_token" not in response.json()
    assert IDENTITY_TOKEN not in response.text
    assert len(workflow.calls) == 1
    call = workflow.calls[0]
    assert call["public_workspace_id"] == WORKSPACE_PUBLIC_ID
    assert call["idempotency_key"] == "dashboard-demo-key-001"
    assert call["request"].customer_id == CUSTOMER_ID
    assert call["request"].identity_token == IDENTITY_TOKEN
    assert call["request"].session_id == f"sarah-dashboard-{RUN_ID}-learning"
    assert call["request"].message == "My headphones continue disconnecting."
    assert call["request"].visitor_id is None


@pytest.mark.asyncio
@pytest.mark.parametrize(("app_env", "enabled"), [("production", True), ("development", False)])
async def test_dashboard_demo_is_unavailable_without_development_and_explicit_opt_in(
    monkeypatch, tmp_path, app_env, enabled,
):
    monkeypatch.setattr(demo_route, "DASHBOARD_DEMO_CONFIG_PATH", tmp_path / "missing.json")
    workflow = FakeWorkflow()
    response = await _post(_app(monkeypatch, app_env=app_env, enabled=enabled, workflow=workflow))

    assert response.status_code == 404
    assert not workflow.calls
    assert IDENTITY_TOKEN not in response.text


@pytest.mark.asyncio
async def test_dashboard_demo_fails_closed_for_missing_or_malformed_config(monkeypatch, tmp_path):
    config_path = tmp_path / ".sarah_dashboard_demo.json"
    monkeypatch.setattr(demo_route, "DASHBOARD_DEMO_CONFIG_PATH", config_path)
    workflow = FakeWorkflow()
    application = _app(monkeypatch, workflow=workflow)

    missing = await _post(application)
    config_path.write_text("{not-json", encoding="utf-8")
    malformed = await _post(application)

    assert missing.status_code == malformed.status_code == 503
    assert missing.json() == malformed.json() == {"detail": "Dashboard demo is unavailable"}
    assert IDENTITY_TOKEN not in missing.text + malformed.text
    assert not workflow.calls


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "overrides",
    [
        {"demo_namespace": "wrong-namespace"},
        {"synthetic_data": False},
        {"workspace_id": "not-a-uuid"},
        {"identity_token": ""},
    ],
)
async def test_dashboard_demo_rejects_untrusted_config(monkeypatch, tmp_path, overrides):
    config_path = tmp_path / ".sarah_dashboard_demo.json"
    _write_config(config_path, **overrides)
    monkeypatch.setattr(demo_route, "DASHBOARD_DEMO_CONFIG_PATH", config_path)
    workflow = FakeWorkflow()

    response = await _post(_app(monkeypatch, workflow=workflow))

    assert response.status_code == 503
    assert response.json() == {"detail": "Dashboard demo is unavailable"}
    assert not workflow.calls


@pytest.mark.asyncio
async def test_browser_cannot_override_demo_identity_fields(monkeypatch, tmp_path):
    config_path = tmp_path / ".sarah_dashboard_demo.json"
    _write_config(config_path)
    monkeypatch.setattr(demo_route, "DASHBOARD_DEMO_CONFIG_PATH", config_path)
    workflow = FakeWorkflow()
    body = {
        "session_id": "dashboard-session-1",
        "message": "Hello.",
        "workspace_id": str(uuid4()),
        "customer_id": str(uuid4()),
        "identity_token": "attacker-controlled",
    }

    response = await _post(_app(monkeypatch, workflow=workflow), body=body)

    assert response.status_code == 400
    assert not workflow.calls
    assert "attacker-controlled" not in response.text


@pytest.mark.asyncio
async def test_dashboard_allows_one_fresh_run_across_learning_and_recall_sessions(monkeypatch, tmp_path):
    config_path = tmp_path / ".sarah_dashboard_demo.json"
    _write_config(config_path)
    monkeypatch.setattr(demo_route, "DASHBOARD_DEMO_CONFIG_PATH", config_path)
    workflow = FakeWorkflow()
    application = _app(monkeypatch, workflow=workflow)

    phase_one = await _post(application, key="dashboard-demo-key-phase-001", body={
        "session_id": f"sarah-dashboard-{RUN_ID}-learning", "message": "Phase one synthetic request"
    })
    phase_two = await _post(application, key="dashboard-demo-key-phase-002", body={
        "session_id": f"sarah-dashboard-{RUN_ID}-learning", "message": "Phase two synthetic request"
    })
    phase_three = await _post(application, key="dashboard-demo-key-phase-003", body={
        "session_id": f"sarah-dashboard-{RUN_ID}-recall", "message": "Phase three synthetic request"
    })

    assert [phase_one.status_code, phase_two.status_code, phase_three.status_code] == [200, 200, 200]
    state = json.loads(config_path.with_name(f"{config_path.name}.run.json").read_text())
    assert state == {"customer_id": CUSTOMER_ID, "active_run_id": RUN_ID}
    assert len(workflow.calls) == 3


@pytest.mark.asyncio
async def test_dashboard_blocks_new_scenario_run_until_reseeded(monkeypatch, tmp_path):
    config_path = tmp_path / ".sarah_dashboard_demo.json"
    _write_config(config_path)
    monkeypatch.setattr(demo_route, "DASHBOARD_DEMO_CONFIG_PATH", config_path)
    workflow = FakeWorkflow()
    application = _app(monkeypatch, workflow=workflow)
    first = await _post(application, key="dashboard-demo-key-run-one", body={
        "session_id": f"sarah-dashboard-{RUN_ID}-learning", "message": "First scenario"
    })
    second_run_id = str(uuid4())
    second = await _post(application, key="dashboard-demo-key-run-two", body={
        "session_id": f"sarah-dashboard-{second_run_id}-learning", "message": "Replay scenario"
    })

    assert first.status_code == 200
    assert second.status_code == 409
    assert "Reseed" in second.json()["detail"]
    assert len(workflow.calls) == 1


@pytest.mark.asyncio
async def test_dashboard_rejects_legacy_config_without_seeded_run_state(monkeypatch, tmp_path):
    config_path = tmp_path / ".sarah_dashboard_demo.json"
    config_path.write_text(json.dumps({
        "workspace_public_id": WORKSPACE_PUBLIC_ID,
        "workspace_id": WORKSPACE_ID,
        "customer_id": CUSTOMER_ID,
        "identity_token": IDENTITY_TOKEN,
        "demo_namespace": demo_route.EXPECTED_DEMO_NAMESPACE,
        "synthetic_data": True,
    }))
    monkeypatch.setattr(demo_route, "DASHBOARD_DEMO_CONFIG_PATH", config_path)
    workflow = FakeWorkflow()
    response = await _post(_app(monkeypatch, workflow=workflow))

    assert response.status_code == 503
    assert not workflow.calls


@pytest.mark.asyncio
@pytest.mark.parametrize("key", [None, "short", "invalid-key-!!!!!!!!"])
async def test_dashboard_demo_rejects_missing_or_invalid_idempotency_key(monkeypatch, tmp_path, key):
    config_path = tmp_path / ".sarah_dashboard_demo.json"
    _write_config(config_path)
    monkeypatch.setattr(demo_route, "DASHBOARD_DEMO_CONFIG_PATH", config_path)
    workflow = FakeWorkflow()

    response = await _post(_app(monkeypatch, workflow=workflow), key=key)

    assert response.status_code == 400
    assert not workflow.calls


@pytest.mark.asyncio
@pytest.mark.parametrize("body", [
    {"session_id": " ", "message": "hello"},
    {"session_id": "session", "message": " "},
    {"session_id": "session", "message": "hello", "visitor_id": str(uuid4())},
])
async def test_dashboard_demo_validates_request_shape_and_nonempty_fields(monkeypatch, tmp_path, body):
    config_path = tmp_path / ".sarah_dashboard_demo.json"
    _write_config(config_path)
    monkeypatch.setattr(demo_route, "DASHBOARD_DEMO_CONFIG_PATH", config_path)
    workflow = FakeWorkflow()

    response = await _post(_app(monkeypatch, workflow=workflow), body=body)

    assert response.status_code == 400
    assert not workflow.calls
