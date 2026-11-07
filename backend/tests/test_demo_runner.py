from datetime import datetime, timedelta, timezone
import hashlib
import json
import logging
from types import SimpleNamespace

import jwt
import pytest
from uuid import UUID

from app.core.config import Settings
import scripts.run_sarah_demo as demo_runner

from scripts.run_sarah_demo import (
    DEFAULT_HTTP_TIMEOUT_SECONDS,
    HTTP_TIMEOUT_ENV,
    build_scenario,
    find_current_failed_attempt_ids,
    get_http_timeout_seconds,
    claim_demo_configuration,
    _interaction_payload,
    _recommends_pairing_step,
    _post_interaction,
    demo_final_decision,
    DemoInteraction,
    DemoIdentityTokenError,
    DemoValidationError,
    validate_phase_one_recommendation,
)
from app.agents.troubleshooting_actions import failed_action_response_status
from app.agents.troubleshooting_actions import recommended_action_ids


def test_demo_timeout_defaults_to_45_seconds(monkeypatch):
    monkeypatch.delenv(HTTP_TIMEOUT_ENV, raising=False)
    assert get_http_timeout_seconds() == DEFAULT_HTTP_TIMEOUT_SECONDS == 45.0


def test_demo_timeout_reads_dedicated_environment_setting(monkeypatch):
    monkeypatch.setenv(HTTP_TIMEOUT_ENV, "180")
    assert get_http_timeout_seconds() == 180.0


@pytest.mark.parametrize("value", ["not-a-number", "nan", "inf", "0", "3600.1", "-1"])
def test_demo_timeout_rejects_invalid_or_unbounded_values(value):
    with pytest.raises(ValueError, match=HTTP_TIMEOUT_ENV):
        get_http_timeout_seconds(value)


def test_fresh_scenario_runs_have_unique_keys_and_session_ids():
    first = build_scenario()
    second = build_scenario()
    assert {item.idempotency_key for item in first}.isdisjoint(
        {item.idempotency_key for item in second}
    )
    assert {item.session_id for item in first}.isdisjoint({item.session_id for item in second})
    assert len({item.idempotency_key for item in first}) == 3
    assert first[0].session_id == first[1].session_id
    assert first[2].session_id != first[0].session_id


def test_scenario_orders_suggestion_failure_then_cross_session_recall():
    run_id = UUID("e32b46d7-1611-4df6-b948-cc29482ad7b1")
    scenario = build_scenario(run_id)
    assert scenario == build_scenario(run_id)
    assert [item.phase for item in scenario] == ["suggest_step", "report_failure", "cross_session_recall"]
    assert "disconnect" in scenario[0].message.lower()
    assert "suggest one different step" in scenario[0].message.lower()
    assert "followed your suggestion" in scenario[1].message.lower()
    assert "did not help" in scenario[1].message.lower()
    assert "previous support history" in scenario[2].message.lower()
    assert len({item.idempotency_key for item in scenario}) == len(scenario)


def test_all_three_phases_share_customer_and_token_but_keep_session_boundaries():
    scenario = build_scenario(UUID("e32b46d7-1611-4df6-b948-cc29482ad7b1"))
    config = {
        "customer_id": "c38f4b96-6e1a-4260-8d5d-51c3d7f1c1bd",
        "identity_token": "synthetic-test-token",
    }
    payloads = [_interaction_payload(config, item) for item in scenario]

    assert {payload["customer_id"] for payload in payloads} == {config["customer_id"]}
    assert {payload["identity_token"] for payload in payloads} == {config["identity_token"]}
    assert [payload["session_id"] for payload in payloads] == [item.session_id for item in scenario]
    assert payloads[0]["session_id"] == payloads[1]["session_id"]
    assert payloads[2]["session_id"] != payloads[0]["session_id"]


def test_demo_configuration_is_single_use_until_reseeded(tmp_path):
    customer_id = "c38f4b96-6e1a-4260-8d5d-51c3d7f1c1bd"
    demo_file = tmp_path / ".sarah_demo.json"
    demo_file.write_text(json.dumps({
        "customer_id": customer_id,
        "demo_run_id": customer_id,
        "demo_namespace": demo_runner.DEMO_NAMESPACE,
        "synthetic_data": True,
        "run_status": "ready",
        "identity_token": "synthetic-test-token",
    }), encoding="utf-8")

    claimed = claim_demo_configuration(demo_file)
    assert claimed["run_status"] == "started"
    assert json.loads(demo_file.read_text(encoding="utf-8"))["run_status"] == "started"
    with pytest.raises(DemoValidationError) as error:
        claim_demo_configuration(demo_file)
    assert error.value.condition == "demo_configuration_already_used_reseed_required"


def test_hindsight_verification_requires_current_customer_reported_failure():
    fingerprint = "a1b2c3d4e5f67890" * 4
    original_statement = build_scenario(UUID("e32b46d7-1611-4df6-b948-cc29482ad7b1"))[1].message
    current = {
        "id": "memory-current",
        # Hindsight may return extracted/paraphrased recall text. The digest binds
        # this record to the exact original statement without requiring verbatim recall.
        "text": "Customer reported that the pairing reset failed.",
        "metadata": {
            "provenance_kind": "failed_attempt",
            "confirmation_source": "customer_report",
            "independently_verified": "false",
            "session_fingerprint": fingerprint,
            "action_ids": "bluetooth_forget_and_pair",
            "linked_to_prior_recommendation": "true",
            "prior_recommendation_message_id": "assistant-prior",
            "customer_statement_sha256": hashlib.sha256(original_statement.encode("utf-8")).hexdigest(),
        },
        "tags": ["provenance:failed_attempt", "confirmation:customer_report"],
    }
    old = {**current, "id": "memory-old", "metadata": {**current["metadata"], "session_fingerprint": "old"}}
    assert find_current_failed_attempt_ids(
        {"results": [old], "source_facts": {"memory-current": current}},
        session_fingerprint=fingerprint,
        statement_sha256=hashlib.sha256(original_statement.encode("utf-8")).hexdigest(),
    ) == {"memory-current"}
    recalled_failure_ids = find_current_failed_attempt_ids(
        {"results": [current], "source_facts": {}}, session_fingerprint=fingerprint,
        statement_sha256=hashlib.sha256(original_statement.encode("utf-8")).hexdigest(),
    )
    assert recalled_failure_ids == {"memory-current"}
    assert failed_action_response_status(
        "Try forgetting these headphones in Bluetooth settings and pair them again.",
        {"bluetooth_forget_and_pair"},
    ) == "repeat"
    assert failed_action_response_status(
        "Check the headphones for a firmware update.", {"bluetooth_forget_and_pair"}
    ) == "avoided"
    assert len(fingerprint) == 64


def test_failed_attempt_verification_rejects_wrong_statement_digest():
    scenario = build_scenario(UUID("e32b46d7-1611-4df6-b948-cc29482ad7b1"))
    statement = scenario[1].message
    record = _valid_failed_attempt_record(statement)
    record["metadata"]["customer_statement_sha256"] = hashlib.sha256(b"different statement").hexdigest()
    assert not find_current_failed_attempt_ids(
        {"results": [record]},
        session_fingerprint=hashlib.sha256(scenario[1].session_id.encode()).hexdigest(),
        statement_sha256=hashlib.sha256(statement.encode()).hexdigest(),
    )


@pytest.mark.parametrize("mutation", [
    lambda record: record["metadata"].update(session_fingerprint="wrong"),
    lambda record: record["metadata"].pop("provenance_kind"),
    lambda record: record["metadata"].pop("confirmation_source"),
    lambda record: record.update(tags=["provenance:failed_attempt"]),
    lambda record: record.update(tags=["confirmation:customer_report"]),
    lambda record: record["metadata"].update(action_ids="different_action"),
    lambda record: record["metadata"].update(linked_to_prior_recommendation="false"),
    lambda record: record["metadata"].pop("prior_recommendation_message_id"),
])
def test_failed_attempt_verification_rejects_each_required_predicate_failure(mutation):
    scenario = build_scenario(UUID("e32b46d7-1611-4df6-b948-cc29482ad7b1"))
    statement = scenario[1].message
    record = _valid_failed_attempt_record(statement)
    mutation(record)
    assert not find_current_failed_attempt_ids(
        {"results": [record]},
        session_fingerprint=hashlib.sha256(scenario[1].session_id.encode()).hexdigest(),
        statement_sha256=hashlib.sha256(statement.encode()).hexdigest(),
    )


def _valid_failed_attempt_record(statement: str) -> dict:
    scenario = build_scenario(UUID("e32b46d7-1611-4df6-b948-cc29482ad7b1"))
    return {
        "id": "memory-id",
        "text": "Extracted summary: the pairing attempt did not solve the disconnection.",
        "metadata": {
            "provenance_kind": "failed_attempt",
            "confirmation_source": "customer_report",
            "independently_verified": "false",
            "session_fingerprint": hashlib.sha256(scenario[1].session_id.encode()).hexdigest(),
            "customer_statement_sha256": hashlib.sha256(statement.encode()).hexdigest(),
            "action_ids": "bluetooth_forget_and_pair",
            "linked_to_prior_recommendation": "true",
            "prior_recommendation_message_id": "opaque-assistant-id",
        },
        "tags": ["provenance:failed_attempt", "confirmation:customer_report"],
    }


def test_later_demo_response_must_not_repeat_the_failed_step():
    assert _recommends_pairing_step(
        "Try forgetting the Bluetooth headphones and pairing them again."
    )
    assert not _recommends_pairing_step(
        "Forgetting the Bluetooth headphones and pairing did not help. Please check whether the firmware is current."
    )
    assert _recommends_pairing_step(
        "Forgetting the Bluetooth headphones and pairing did not help, so try forgetting the Bluetooth headphones and pairing them again."
    )
    assert not _recommends_pairing_step(
        "Do not try forgetting the Bluetooth headphones and pairing them again. Check the firmware instead."
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "results",
    [
        [{"id": "old", "metadata": {"provenance_kind": "failed_attempt"}, "tags": []}],
        [{"id": "old", "metadata": {}, "tags": ["provenance:failed_attempt"]}],
    ],
)
async def test_demo_preflight_blocks_a_reused_bank_with_prior_failures(monkeypatch, caplog, results):
    caplog.set_level(logging.INFO, logger="uvicorn.error.sarah_demo_preflight")
    class FakeSettings:
        hindsight_api_key = "configured"
        hindsight_bank_id_secret = "configured"
        identity_token_secret = "configured"
        identity_token_issuer = "issuer"
        identity_token_audience = "audience"

    class FakeClient:
        async def aclose(self):
            pass

    class FakeMemoryService:
        def __init__(self, client, *, bank_id_secret):
            assert bank_id_secret == "configured"

        async def recall_memories(self, *args, **kwargs):
            assert kwargs["tags"] == ["provenance:failed_attempt"]
            assert kwargs["tags_match"] == "all_strict"
            return {"results": results, "source_facts": {}}

    monkeypatch.setattr(demo_runner, "Settings", lambda **kwargs: FakeSettings())
    monkeypatch.setattr(demo_runner, "verify_identity_token", lambda *args, **kwargs: SimpleNamespace(
        workspace_id="workspace-safe", subject_id="subject-safe"
    ))
    monkeypatch.setattr(demo_runner, "create_hindsight_client", lambda settings: FakeClient())
    monkeypatch.setattr(demo_runner, "MemoryService", FakeMemoryService)
    config = {"identity_token": "private-token", "workspace_id": "workspace-safe", "customer_id": "subject-safe"}

    with pytest.raises(DemoValidationError) as raised:
        await demo_runner._verify_clean_demo_bank(config)

    assert raised.value.phase == "preflight"
    assert raised.value.condition == "demo_bank_not_clean_reseed_required"
    assert "prior_failed_attempt_present" in caplog.text
    assert "private-token" not in caplog.text


@pytest.mark.asyncio
async def test_demo_preflight_accepts_clean_synthetic_baseline(monkeypatch, caplog):
    caplog.set_level(logging.INFO, logger="uvicorn.error.sarah_demo_preflight")
    class FakeSettings:
        hindsight_api_key = "configured"
        hindsight_bank_id_secret = "configured"
        identity_token_secret = "configured"
        identity_token_issuer = "issuer"
        identity_token_audience = "audience"

    class FakeClient:
        async def aclose(self):
            self.closed = True

    client = FakeClient()

    class FakeMemoryService:
        def __init__(self, client_arg, *, bank_id_secret):
            assert client_arg is client

        async def recall_memories(self, *args, **kwargs):
            return {"results": [{"id": "baseline", "metadata": {"fixture_id": "baseline"},
                                 "tags": ["synthetic_demo", "failed_attempt"]}], "source_facts": {}}

    monkeypatch.setattr(demo_runner, "Settings", lambda **kwargs: FakeSettings())
    monkeypatch.setattr(demo_runner, "verify_identity_token", lambda *args, **kwargs: SimpleNamespace(
        workspace_id="workspace-safe", subject_id="subject-safe"
    ))
    monkeypatch.setattr(demo_runner, "create_hindsight_client", lambda settings: client)
    monkeypatch.setattr(demo_runner, "MemoryService", FakeMemoryService)

    await demo_runner._verify_clean_demo_bank({
        "identity_token": "private-token", "workspace_id": "workspace-safe", "customer_id": "subject-safe"
    })

    assert client.closed is True
    assert "sarah_demo_bank_preflight outcome=clean" in caplog.text
    assert "private-token" not in caplog.text


def test_phase_one_requires_the_specific_action_phase_two_reports():
    validate_phase_one_recommendation(
        "Please forget the Bluetooth headphones in settings, then pair them again."
    )

    # A factory reset is not the forget-and-pair action that Phase 2 claims Sarah tried.
    with pytest.raises(DemoValidationError) as error:
        validate_phase_one_recommendation(
            "Perform a factory reset on your headphones, then pair them again."
        )

    assert error.value.phase == "phase1"
    assert error.value.condition == "required_forget_and_pair_action_not_detected"
    assert str(error.value) == (
        "phase=phase1 condition=required_forget_and_pair_action_not_detected"
    )


def test_phase_one_accepts_the_exact_multistep_forget_and_pair_response():
    response = (
        "Find the headphones in Bluetooth settings. Select ‘Forget’ or ‘Remove’ the device. "
        "Turn Bluetooth off and on. Put the headphones into pairing mode. Pair them again."
    )

    validate_phase_one_recommendation(response)
    assert recommended_action_ids(response) == {"bluetooth_forget_and_pair"}


def test_multistep_matcher_does_not_accept_generic_bluetooth_troubleshooting():
    assert not recommended_action_ids(
        "Turn Bluetooth off and on. Restart the headphones and check for a firmware update."
    )


@pytest.mark.asyncio
async def test_phase_one_mismatch_stops_before_phase_two_request(monkeypatch, tmp_path, capsys):
    import httpx

    workspace_id = "4fca82f2-0c2e-44f2-9a72-019003044c1d"
    customer_id = "c38f4b96-6e1a-4260-8d5d-51c3d7f1c1bd"
    demo_file = tmp_path / ".sarah_demo.json"
    demo_file.write_text(json.dumps({
        "workspace_public_id": workspace_id,
        "workspace_id": workspace_id,
        "customer_id": customer_id,
        "demo_run_id": customer_id,
        "run_status": "ready",
        "identity_token": "synthetic-test-token",
        "demo_namespace": demo_runner.DEMO_NAMESPACE,
        "synthetic_data": True,
    }), encoding="utf-8")
    monkeypatch.setattr(demo_runner, "DEMO_FILE", demo_file)
    monkeypatch.setattr(demo_runner, "verify_demo_identity_config", lambda config: None)

    async def clean_bank(config):
        return None

    monkeypatch.setattr(demo_runner, "_verify_clean_demo_bank", clean_bank)

    class FakeClient:
        def __init__(self):
            self.posts = 0

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return None

        async def post(self, *args, **kwargs):
            self.posts += 1
            return httpx.Response(
                200,
                headers={"X-Workflow-Status": "complete", "X-Memory-Status": "stored"},
                json={"response": "Perform a factory reset on your headphones, then pair them again."},
                request=httpx.Request("POST", "http://test/api/v1/chat"),
            )

    fake_client = FakeClient()
    monkeypatch.setattr(demo_runner.httpx, "AsyncClient", lambda **kwargs: fake_client)

    with pytest.raises(DemoValidationError) as error:
        await demo_runner.run()

    assert fake_client.posts == 1
    assert error.value.phase == "phase1"
    assert error.value.condition == "required_forget_and_pair_action_not_detected"
    # The runner currently prints the phase-one reply before validating the action.
    assert "factory reset" in capsys.readouterr().out.lower()
    assert json.loads(demo_file.read_text(encoding="utf-8"))["run_status"] == "started"


def test_main_reports_phase_and_condition_without_exception_details(monkeypatch, capsys):
    def fail_with_validation_error(coroutine):
        coroutine.close()
        raise DemoValidationError("phase3", "failed_action_recommended_again")

    monkeypatch.setattr(demo_runner.asyncio, "run", fail_with_validation_error)
    with pytest.raises(SystemExit) as error:
        demo_runner.main()

    assert error.value.code == 1
    output = capsys.readouterr().out
    assert "phase=phase3" in output
    assert "condition=failed_action_recommended_again" in output
    assert "traceback" not in output.lower()


def test_final_avoidance_check_targets_the_failed_action():
    assert failed_action_response_status(
        "Try forgetting the headphones in Bluetooth settings and pairing them again.",
        {"bluetooth_forget_and_pair"},
    ) == "repeat"
    assert failed_action_response_status(
        "Check for a firmware update and test the headphones again.",
        {"bluetooth_forget_and_pair"},
    ) == "avoided"


@pytest.mark.parametrize("response", [
    "Try removing the headphones from Bluetooth's saved devices and pair them from scratch.",
    "Unpair the earbuds, then pair them again from the Bluetooth menu.",
    "Forget the headset in Bluetooth settings and start pairing again.",
    "Delete the saved Bluetooth pairing and start setup again.",
])
def test_demo_validator_detects_pairing_paraphrases(response):
    assert failed_action_response_status(response, {"bluetooth_forget_and_pair"}) == "repeat"


def test_demo_validator_marks_semantically_uncertain_response_for_human_review():
    assert failed_action_response_status(
        "Try a fresh setup for the saved Bluetooth headphones.",
        {"bluetooth_forget_and_pair"},
    ) == "uncertain"
    assert not demo_final_decision("uncertain", "no")
    assert not demo_final_decision("uncertain", "yes", relevant_memory_used=False)
    assert demo_final_decision("uncertain", "yes")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("status", "headers"),
    [
        (202, {"X-Workflow-Status": "escalation-pending"}),
        (200, {"X-Memory-Status": "failed"}),
        (200, {"X-Workflow-Status": "response_persisted"}),
    ],
)
async def test_post_interaction_rejects_partial_or_failed_status(status, headers):
    import httpx

    class FakeClient:
        async def post(self, *args, **kwargs):
            return httpx.Response(status, headers=headers, json={"response": "partial"}, request=httpx.Request("POST", "http://test"))

    interaction = DemoInteraction("phase", "session-x", "idempotency-key-001", "hello")
    with pytest.raises(RuntimeError, match="incomplete|status"):
        await _post_interaction(FakeClient(), {
            "workspace_public_id": "workspace", "customer_id": "customer", "identity_token": "token",
        }, interaction)


@pytest.mark.asyncio
async def test_runner_rejects_expired_signed_demo_token_before_http_request(monkeypatch, tmp_path):
    now = datetime.now(timezone.utc)
    secret = "local-test-identity-secret-with-enough-entropy"
    workspace_id = str(UUID("4fca82f2-0c2e-44f2-9a72-019003044c1d"))
    customer_id = str(UUID("c38f4b96-6e1a-4260-8d5d-51c3d7f1c1bd"))
    token = jwt.encode(
        {
            "exp": now - timedelta(seconds=1),
            "iat": now - timedelta(hours=1),
            "iss": "demo-test-issuer",
            "aud": "demo-test-audience",
            "identity_type": "customer",
            "workspace_id": workspace_id,
            "customer_id": customer_id,
        },
        secret,
        algorithm="HS256",
    )
    settings = Settings(
        identity_token_secret=secret,
        identity_token_issuer="demo-test-issuer",
        identity_token_audience="demo-test-audience",
        _env_file=None,
    )
    demo_file = tmp_path / ".sarah_demo.json"
    demo_file.write_text(json.dumps({
        "workspace_public_id": workspace_id,
        "workspace_id": workspace_id,
        "customer_id": customer_id,
        "demo_run_id": customer_id,
        "run_status": "ready",
        "identity_token": token,
        "demo_namespace": demo_runner.DEMO_NAMESPACE,
        "synthetic_data": True,
    }), encoding="utf-8")
    monkeypatch.setattr(demo_runner, "DEMO_FILE", demo_file)
    monkeypatch.setattr(demo_runner, "Settings", lambda **_: settings)

    def no_http_client(*args, **kwargs):
        raise AssertionError("HTTP client must not be created for an expired token")

    monkeypatch.setattr(demo_runner.httpx, "AsyncClient", no_http_client)
    with pytest.raises(DemoIdentityTokenError) as error:
        await demo_runner.run()
    assert token not in str(error.value)


@pytest.mark.asyncio
async def test_hindsight_verification_uses_customer_bank_strict_failed_attempt_tags(monkeypatch):
    interaction = build_scenario(UUID("e32b46d7-1611-4df6-b948-cc29482ad7b1"))[1]
    workspace_id = "d43a3f2a-4381-4fb1-9376-281d8f4e31b8"
    customer_id = "c38f4b96-6e1a-4260-8d5d-51c3d7f1c1bd"
    session_fingerprint = hashlib.sha256(interaction.session_id.encode()).hexdigest()
    memory_record = {
        "id": "opaque-memory-id",
        "text": interaction.message,
        "metadata": {
            "provenance_kind": "failed_attempt",
            "confirmation_source": "customer_report",
            "independently_verified": "false",
            "session_fingerprint": session_fingerprint,
            "action_ids": "bluetooth_forget_and_pair",
            "linked_to_prior_recommendation": "true",
            "prior_recommendation_message_id": "opaque-assistant-id",
            "customer_statement_sha256": hashlib.sha256(interaction.message.encode()).hexdigest(),
        },
        "tags": ["provenance:failed_attempt", "outcome:reported_failed", "confirmation:customer_report"],
    }
    settings = SimpleNamespace(
        hindsight_api_key=object(),
        hindsight_bank_id_secret="test-secret",
        identity_token_secret=object(),
        identity_token_issuer="issuer",
        identity_token_audience="audience",
    )
    identity = SimpleNamespace(workspace_id=workspace_id, subject_id=customer_id)
    query_calls = []

    class FakeHindsight:
        async def aclose(self):
            pass

    class FakeMemoryService:
        def __init__(self, client, *, bank_id_secret):
            assert client is hindsight_client
            assert bank_id_secret == "test-secret"

        async def recall_memories(self, *args, **kwargs):
            query_calls.append((args, kwargs))
            return {"results": [memory_record], "source_facts": {}}

    hindsight_client = FakeHindsight()
    monkeypatch.setattr(demo_runner, "Settings", lambda **kwargs: settings)
    monkeypatch.setattr(demo_runner, "verify_identity_token", lambda *args, **kwargs: identity)
    monkeypatch.setattr(demo_runner, "create_hindsight_client", lambda settings: hindsight_client)
    monkeypatch.setattr(demo_runner, "MemoryService", FakeMemoryService)

    result = await demo_runner._verify_hindsight_failure(
        {"identity_token": "synthetic-token", "workspace_id": workspace_id, "customer_id": customer_id},
        interaction,
    )

    assert result == {"opaque-memory-id"}
    assert len(query_calls) == 1
    args, kwargs = query_calls[0]
    assert args[:2] == (workspace_id, customer_id)
    assert kwargs["subject_type"] == "customer"
    assert kwargs["tags"] == ["provenance:failed_attempt"]
    assert kwargs["tags_match"] == "all_strict"
    assert "identity_token" not in str(query_calls)


@pytest.mark.asyncio
async def test_hindsight_verification_miss_is_diagnosed_without_retry_or_pii(monkeypatch, caplog):
    interaction = build_scenario(UUID("e32b46d7-1611-4df6-b948-cc29482ad7b1"))[1]
    workspace_id = "d43a3f2a-4381-4fb1-9376-281d8f4e31b8"
    customer_id = "c38f4b96-6e1a-4260-8d5d-51c3d7f1c1bd"
    settings = SimpleNamespace(
        hindsight_api_key=object(),
        hindsight_bank_id_secret="test-secret",
        identity_token_secret=object(),
        identity_token_issuer="issuer",
        identity_token_audience="audience",
    )
    identity = SimpleNamespace(workspace_id=workspace_id, subject_id=customer_id)
    calls = []

    class FakeHindsight:
        async def aclose(self):
            pass

    class FakeMemoryService:
        def __init__(self, client, *, bank_id_secret):
            pass

        async def recall_memories(self, *args, **kwargs):
            calls.append((args, kwargs))
            return {"results": [], "source_facts": {}}

    hindsight_client = FakeHindsight()
    monkeypatch.setattr(demo_runner, "Settings", lambda **kwargs: settings)
    monkeypatch.setattr(demo_runner, "verify_identity_token", lambda *args, **kwargs: identity)
    monkeypatch.setattr(demo_runner, "create_hindsight_client", lambda settings: hindsight_client)
    monkeypatch.setattr(demo_runner, "MemoryService", FakeMemoryService)
    caplog.set_level("WARNING", logger="uvicorn.error.sarah_demo_verification")

    with pytest.raises(DemoValidationError) as error:
        await demo_runner._verify_hindsight_failure(
            {"identity_token": "synthetic-token", "workspace_id": workspace_id, "customer_id": customer_id},
            interaction,
        )

    assert error.value.condition == "current_failed_attempt_not_found"
    assert len(calls) == 1
    assert "sarah_demo_failed_attempt_verification outcome=query_miss reason=no_tagged_results" in caplog.text
    assert interaction.message not in caplog.text
    assert customer_id not in caplog.text
    assert "candidate_present=false" in caplog.text
    assert "statement_digest_match=false" in caplog.text


def test_predicate_diagnostics_are_boolean_only_and_individual(caplog):
    scenario = build_scenario(UUID("e32b46d7-1611-4df6-b948-cc29482ad7b1"))
    statement = scenario[1].message
    record = _valid_failed_attempt_record(statement)
    record["metadata"]["session_fingerprint"] = "wrong"
    caplog.set_level("INFO", logger="uvicorn.error.sarah_demo_verification")

    ids = demo_runner._log_failed_attempt_predicates(
        [record],
        session_fingerprint=hashlib.sha256(scenario[1].session_id.encode()).hexdigest(),
        statement_sha256=hashlib.sha256(statement.encode()).hexdigest(),
    )

    assert not ids
    message = caplog.text
    assert "session_fingerprint_match=false" in message
    assert "statement_digest_match=true" in message
    assert statement not in message
    assert record["text"] not in message
    assert "opaque-assistant-id" not in message
    assert "bluetooth_forget_and_pair" not in message
    assert "wrong" not in message
