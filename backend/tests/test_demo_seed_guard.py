import json
from pydantic import AnyHttpUrl
import pytest
from uuid import UUID
from fastapi import HTTPException

from app.core.config import Settings
from app.core.security import verify_identity_token
from app.memory.memory_service import MemoryService
from scripts.seed_sarah_demo import (
    EXTERNAL_ID,
    create_demo_identity_token,
    history_session_id,
    new_synthetic_customer_payload,
    seed_history_memory_once,
    validate_demo_target,
    write_sarah_demo_configs,
)


def demo_settings():
    return Settings(
        supabase_url=AnyHttpUrl("https://approved-ref.supabase.co"),
        demo_supabase_project_ref="approved-ref",
        demo_supabase_project_allowlist="approved-ref,other-ref",
        _env_file=None,
    )


def enable(monkeypatch, *, app_env="development", opt_in="true"):
    monkeypatch.setenv("APP_ENV", app_env)
    monkeypatch.setenv("ALLOW_SYNTHETIC_DEMO_SEED", opt_in)


def test_demo_seed_requires_explicit_app_env(monkeypatch):
    monkeypatch.delenv("APP_ENV", raising=False)
    monkeypatch.setenv("ALLOW_SYNTHETIC_DEMO_SEED", "true")
    with pytest.raises(RuntimeError, match="explicitly set"):
        validate_demo_target(demo_settings())


def test_demo_seed_rejects_production_app_env(monkeypatch):
    enable(monkeypatch, app_env="production")
    with pytest.raises(RuntimeError, match="APP_ENV"):
        validate_demo_target(demo_settings())


def test_demo_seed_requires_explicit_opt_in(monkeypatch):
    enable(monkeypatch, opt_in="false")
    with pytest.raises(RuntimeError, match="ALLOW_SYNTHETIC_DEMO_SEED"):
        validate_demo_target(demo_settings())


def test_demo_seed_rejects_mismatched_supabase_project(monkeypatch):
    enable(monkeypatch)
    settings = demo_settings().model_copy(update={"supabase_url": AnyHttpUrl("https://production-ref.supabase.co")})
    with pytest.raises(RuntimeError, match="does not match"):
        validate_demo_target(settings)


def test_demo_seed_requires_project_allowlist(monkeypatch):
    enable(monkeypatch)
    settings = demo_settings().model_copy(update={"demo_supabase_project_allowlist": "other-ref"})
    with pytest.raises(RuntimeError, match="not allowlisted"):
        validate_demo_target(settings)


def test_demo_seed_rejects_unknown_non_hosted_target(monkeypatch):
    enable(monkeypatch)
    settings = demo_settings().model_copy(update={"supabase_url": AnyHttpUrl("http://127.0.0.1:54321")})
    with pytest.raises(RuntimeError, match="does not match"):
        validate_demo_target(settings)


def test_seeder_writes_separate_private_dashboard_config_without_changing_cli_shape(tmp_path):
    workspace_public_id = "bafef055-9d7c-41a5-84e6-5376e29a2f51"
    workspace_id = "d43a3f2a-4381-4fb1-9376-281d8f4e31b8"
    customer_id = "c38f4b96-6e1a-4260-8d5d-51c3d7f1c1bd"
    test_token = "synthetic-token-for-test-only"

    cli_path, dashboard_path = write_sarah_demo_configs(
        tmp_path,
        workspace_public_id=workspace_public_id,
        workspace_id=workspace_id,
        customer_id=customer_id,
        identity_token=test_token,
    )

    cli_config = json.loads(cli_path.read_text(encoding="utf-8"))
    dashboard_config = json.loads(dashboard_path.read_text(encoding="utf-8"))
    assert set(cli_config) == {
        "workspace_public_id", "workspace_id", "customer_id", "identity_token",
        "demo_namespace", "demo_run_id", "run_status", "synthetic_data",
    }
    assert cli_config["run_status"] == "ready"
    assert cli_config["demo_run_id"] == customer_id
    assert set(dashboard_config) == {
        "workspace_public_id", "workspace_id", "customer_id", "identity_token",
        "demo_namespace", "synthetic_data",
    }
    assert dashboard_config["synthetic_data"] is True
    assert dashboard_config["demo_namespace"] == EXTERNAL_ID
    assert dashboard_config["workspace_public_id"] == cli_config["workspace_public_id"]
    assert dashboard_config["workspace_id"] == cli_config["workspace_id"]
    assert dashboard_config["customer_id"] == cli_config["customer_id"]
    assert dashboard_config["identity_token"] == cli_config["identity_token"]
    state_path = dashboard_path.with_name(f"{dashboard_path.name}.run.json")
    assert json.loads(state_path.read_text(encoding="utf-8")) == {
        "customer_id": customer_id,
        "active_run_id": None,
    }
    assert cli_path.stat().st_mode & 0o777 == 0o600
    assert dashboard_path.stat().st_mode & 0o777 == 0o600
    assert state_path.stat().st_mode & 0o777 == 0o600


@pytest.mark.asyncio
async def test_repeated_demo_seeding_does_not_duplicate_or_replace_baseline_memory():
    class Memory:
        def __init__(self):
            self.records = []
            self.retains = []

        async def recall_memories(self, *args, **kwargs):
            return {"results": list(self.records), "source_facts": {}}

        async def retain_memory(self, workspace_id, customer_id, content, **kwargs):
            self.retains.append((workspace_id, customer_id, content, kwargs))
            self.records.append({"id": "fixture-memory", "text": content,
                                 "metadata": kwargs["metadata"], "tags": kwargs["tags"]})

    memory = Memory()
    assert await seed_history_memory_once(memory, "workspace-a", "customer-a") is True
    assert await seed_history_memory_once(memory, "workspace-a", "customer-a") is False
    assert len(memory.retains) == 1
    assert memory.retains[0][3]["document_id"] == "synthetic-sarah-history-baseline-v1"
    assert memory.retains[0][3]["update_mode"] == "append"
    baseline = memory.retains[0][2]
    assert "Restarting Bluetooth and the headphones" in baseline
    assert "did not help" in baseline
    assert "forgetting" not in baseline.lower()
    assert "pairing" not in baseline.lower()
    assert memory.retains[0][3]["metadata"]["fixture_id"] == "sarah-history-baseline-v1"


def test_fresh_synthetic_customer_runs_get_distinct_ids_and_memory_banks():
    workspace_id = "d43a3f2a-4381-4fb1-9376-281d8f4e31b8"
    first = new_synthetic_customer_payload(workspace_id)
    second = new_synthetic_customer_payload(workspace_id)

    assert UUID(first["id"]) != UUID(second["id"])
    assert first["workspace_id"] == second["workspace_id"] == workspace_id
    assert first["name"] == second["name"] == "Sarah Mitchell"
    assert first["identity_verified"] is second["identity_verified"] is True
    assert first["email"] is second["email"] is None
    assert first["external_id"] == f"{EXTERNAL_ID}:{first['id']}"
    assert second["external_id"] == f"{EXTERNAL_ID}:{second['id']}"

    memory = MemoryService(client=None, bank_id_secret="test-bank-id-secret")  # type: ignore[arg-type]
    assert memory.bank_id(workspace_id, first["id"], subject_type="customer") != memory.bank_id(
        workspace_id, second["id"], subject_type="customer"
    )
    assert history_session_id(first["id"]) != history_session_id(second["id"])


@pytest.mark.asyncio
async def test_fresh_run_bank_cannot_recall_previous_runs_failed_attempt():
    class IsolatedHindsight:
        def __init__(self):
            self.banks = {}

        async def acreate_bank(self, *, bank_id, **kwargs):
            self.banks.setdefault(bank_id, [])

        async def aretain(self, *, bank_id, content, metadata=None, tags=None, **kwargs):
            self.banks.setdefault(bank_id, []).append({
                "id": f"memory-{len(self.banks[bank_id])}",
                "text": content,
                "metadata": metadata or {},
                "tags": tags or [],
            })
            return {"success": True}

        async def arecall(self, *, bank_id, **kwargs):
            required_tags = set(kwargs.get("tags") or [])
            return {
                "results": [
                    record for record in self.banks.get(bank_id, [])
                    if required_tags.issubset(set(record["tags"]))
                ],
                "source_facts": {},
            }

    workspace_id = "d43a3f2a-4381-4fb1-9376-281d8f4e31b8"
    first = new_synthetic_customer_payload(workspace_id)
    second = new_synthetic_customer_payload(workspace_id)
    client = IsolatedHindsight()
    memory = MemoryService(client, bank_id_secret="test-bank-id-secret")  # type: ignore[arg-type]

    await memory.retain_memory(
        workspace_id,
        first["id"],
        "A previous run's Bluetooth pairing action failed.",
        subject_type="customer",
        metadata={"provenance_kind": "failed_attempt", "confirmation_source": "customer_report"},
        tags=["provenance:failed_attempt"],
    )
    first_bank = memory.bank_id(workspace_id, first["id"], subject_type="customer")
    second_bank = memory.bank_id(workspace_id, second["id"], subject_type="customer")
    assert first_bank != second_bank
    assert await seed_history_memory_once(memory, workspace_id, second["id"]) is True

    second_history = await memory.recall_memories(
        workspace_id, second["id"], "previous failed pairing", subject_type="customer",
        tags=["provenance:failed_attempt"], tags_match="all_strict",
    )
    assert not second_history["results"]


@pytest.mark.asyncio
async def test_clean_sarah_baseline_does_not_contain_an_old_pairing_failure():
    class Memory:
        def __init__(self):
            self.records = []

        async def recall_memories(self, *args, **kwargs):
            return {"results": self.records, "source_facts": {}}

        async def retain_memory(self, workspace_id, customer_id, content, **kwargs):
            self.records.append({"id": "baseline", "text": content,
                                 "metadata": kwargs["metadata"], "tags": kwargs["tags"]})

    memory = Memory()
    assert await seed_history_memory_once(memory, "workspace-a", "customer-a") is True
    assert not any(
        record["metadata"].get("provenance_kind") == "failed_attempt"
        or "provenance:failed_attempt" in record["tags"]
        for record in memory.records
    )


def test_demo_token_is_short_lived_customer_identity_bound_to_workspace_and_subject():
    secret = "test-identity-secret-that-is-long-enough-000001"
    workspace_id = "d43a3f2a-4381-4fb1-9376-281d8f4e31b8"
    customer_id = "c38f4b96-6e1a-4260-8d5d-51c3d7f1c1bd"
    settings = Settings(
        identity_token_secret=secret,
        identity_token_issuer="demo-issuer",
        identity_token_audience="demo-audience",
        identity_token_max_ttl_seconds=3600,
        _env_file=None,
    )
    signed_token = create_demo_identity_token(settings, workspace_id, customer_id)

    verified = verify_identity_token(
        signed_token, workspace_id=workspace_id, expected_customer_id=customer_id, settings=settings
    )
    assert verified.identity_type == "customer"
    assert verified.subject_id == customer_id
    with pytest.raises(HTTPException):
        verify_identity_token(
            signed_token, workspace_id="f4b1a9bf-0164-4695-9ae9-9fa9a7bd26a1",
            expected_customer_id=customer_id, settings=settings,
        )
    with pytest.raises(HTTPException):
        verify_identity_token(
            signed_token, workspace_id=workspace_id,
            expected_customer_id="00000000-0000-0000-0000-000000000001", settings=settings,
        )
