import json
import logging
from copy import deepcopy
from logging.config import dictConfig
from types import SimpleNamespace
from uuid import uuid4

import httpx
import pytest
from uvicorn.config import LOGGING_CONFIG
from groq import (
    APIConnectionError,
    APITimeoutError,
    AuthenticationError,
    BadRequestError,
    InternalServerError,
    RateLimitError,
)

from app.core.config import Settings
from app.core.security import VerifiedIdentity
from app.memory.memory_service import MemoryRetrievalError
from app.agents.support_agent import (
    GroqGenerationError,
    InvalidAgentOutputError,
    SupportAgent,
)


class FakeMemoryService:
    def __init__(self, results=None, error=None, timeline=None, source_facts=None) -> None:
        self.results = results if results is not None else []
        self.source_facts = source_facts if source_facts is not None else {}
        self.error = error
        self.timeline = timeline if timeline is not None else []
        self.calls = []

    async def recall_memories(self, workspace_id, subject_id, query, *, subject_type):
        self.timeline.append("recall")
        self.calls.append((workspace_id, subject_id, subject_type, query))
        if self.error:
            raise self.error
        return {"results": self.results, "source_facts": self.source_facts}


class FakeGroq:
    def __init__(self, contents=None, *, error=None, timeline=None) -> None:
        self.contents = list(contents or [])
        self.error = error
        self.timeline = timeline if timeline is not None else []
        self.calls = []
        self.chat = SimpleNamespace(completions=self)

    async def create(self, **kwargs):
        self.timeline.append("generate")
        self.calls.append(kwargs)
        if self.error:
            raise self.error
        content = self.contents.pop(0)
        message = SimpleNamespace(content=content)
        return SimpleNamespace(choices=[SimpleNamespace(message=message)])


class CapturingHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.records = []

    def emit(self, record):
        self.records.append(record)


def output_json(**overrides) -> str:
    output = {
        "response": "I understand this has been frustrating. Let's take it one step at a time.",
        "sentiment": "frustrated",
        "memories_used": [],
        "memory_retrieved": False,
        "escalation_required": False,
        "escalation_reason": "",
        "interaction_summary": "The customer reports an unresolved problem.",
        "suggested_memory_facts": ["The customer reports the problem is unresolved."],
    }
    output.update(overrides)
    return json.dumps(output)


def build_agent(memory, groq, *, model="openai/gpt-oss-120b"):
    return SupportAgent(
        settings=Settings(groq_model=model, _env_file=None),
        memory_service=memory,
        groq_client=groq,
    )


def build_budget_agent(memory, groq, *, budget=8192):
    return SupportAgent(
        settings=Settings(groq_context_budget_bytes=budget, _env_file=None),
        memory_service=memory,
        groq_client=groq,
    )


def identity(subject_type="customer", subject_id=None, workspace="workspace-a"):
    return VerifiedIdentity(
        workspace_id=workspace,
        identity_type=subject_type,
        subject_id=subject_id or str(uuid4()),
    )


@pytest.mark.asyncio
async def test_memory_is_retrieved_before_generation_and_used_ids_are_bounded() -> None:
    timeline = []
    memory = FakeMemoryService(results=[{"id": "mem-1", "text": "A prior step failed."}], timeline=timeline)
    groq = FakeGroq([output_json(memories_used=["mem-1", "made-up-id"], memory_retrieved=False)], timeline=timeline)
    agent = build_agent(memory, groq)
    result = await agent.respond(
        workspace_id="workspace-a",
        identity=identity(),
        current_message="The connection is still broken.",
    )
    assert timeline == ["recall", "generate"]
    assert result.memories_used == ["mem-1"]
    assert result.memory_retrieved is True
    assert groq.calls[0]["response_format"]["type"] == "json_schema"


@pytest.mark.asyncio
async def test_failed_troubleshooting_and_preferences_are_in_generation_context() -> None:
    memory = FakeMemoryService(results=[
        {"id": "mem-failed", "text": "Restarting the router was attempted and did not help."},
        {"id": "mem-pref", "text": "Customer prefers one step at a time."},
    ])
    groq = FakeGroq([output_json(memories_used=["mem-failed", "mem-pref"])])
    result = await build_agent(memory, groq).respond(
        workspace_id="workspace-a",
        identity=identity(),
        current_message="It still disconnects.",
        authorized_business_context="Known support hours: weekdays.",
    )
    context = json.loads(groq.calls[0]["messages"][1]["content"])
    history = json.dumps(context["historical_customer_memories"])
    assert "did not help" in history
    assert "one step at a time" in history
    assert "weekdays" in context["authorized_business_context"]
    assert "failed troubleshooting" in groq.calls[0]["messages"][0]["content"].lower()
    assert "one step at a time" in result.response


@pytest.mark.asyncio
async def test_recalled_provenance_metadata_and_tags_reach_generation_context():
    memory = FakeMemoryService(results=[{
        "id": "suggestion-1",
        "text": "Try resetting the device.",
        "metadata": {"provenance_kind": "model_suggestion", "suggestions_unverified": "true"},
        "tags": ["provenance:model_suggestion", "suggestions:unverified"],
    }])
    groq = FakeGroq([output_json()])
    await build_agent(memory, groq).respond(
        workspace_id="workspace-a", identity=identity(), current_message="What should I do?"
    )
    context = json.loads(groq.calls[0]["messages"][1]["content"])
    fact = context["historical_customer_memories"][0]
    assert fact["provenance"] == "model_suggestion"
    assert fact["metadata"]["suggestions_unverified"] == "true"
    assert "provenance:model_suggestion" in fact["tags"]
    assert "never be described as attempted" in groq.calls[0]["messages"][0]["content"]


@pytest.mark.asyncio
async def test_source_fact_provenance_is_available_to_agent_and_can_be_used():
    failed = {
        "id": "failed-source-1",
        "text": "Forgetting and pairing the headphones did not help.",
        "metadata": {
            "provenance_kind": "failed_attempt",
            "confirmation_source": "customer_report",
            "independently_verified": "false",
        },
        "tags": ["provenance:failed_attempt", "confirmation:customer_report"],
    }
    memory = FakeMemoryService(source_facts={"failed-source-1": failed})
    groq = FakeGroq([output_json(memories_used=["failed-source-1"])])
    result = await build_agent(memory, groq).respond(
        workspace_id="workspace-a", identity=identity(), current_message="What should I try next?"
    )
    context = json.loads(groq.calls[0]["messages"][1]["content"])
    recalled = context["historical_customer_memories"][0]
    assert recalled["provenance"] == "failed_attempt"
    assert recalled["metadata"]["confirmation_source"] == "customer_report"
    assert "provenance:failed_attempt" in recalled["tags"]
    assert result.memories_used == ["failed-source-1"]


def failed_pairing_memory():
    return {
        "id": "failed-pairing",
        "text": "The customer reported that forgetting the headphones and pairing again did not help.",
        "metadata": {
            "provenance_kind": "failed_attempt",
            "confirmation_source": "customer_report",
            "independently_verified": "false",
            "reported_outcome": "failed",
            "action_ids": "bluetooth_forget_and_pair",
        },
        "tags": ["provenance:failed_attempt", "confirmation:customer_report"],
    }


@pytest.mark.asyncio
async def test_customer_reported_failed_action_is_hard_constraint_not_only_used_memory():
    memory = FakeMemoryService(source_facts={"failed-pairing": failed_pairing_memory()})
    groq = FakeGroq([output_json(response="Check whether the headphones need a firmware update.")])
    result = await build_agent(memory, groq).respond(
        workspace_id="workspace-a", identity=identity(), current_message="What next?"
    )
    prompt_context = json.loads(groq.calls[0]["messages"][1]["content"])
    assert prompt_context["failed_action_constraints"] == ["bluetooth_forget_and_pair"]
    assert result.memories_used == []


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "repeat",
    [
        "Try removing the headphones from Bluetooth's saved devices and pair them from scratch.",
        "Unpair the earbuds, then pair them again from the Bluetooth menu.",
    ],
)
async def test_repeated_failed_action_paraphrase_is_retried_then_rejected(repeat):
    groq = FakeGroq([
        output_json(response=repeat),
        output_json(response="Please forget the Bluetooth headphones and pair them again."),
    ])
    result = await build_agent(
        FakeMemoryService(source_facts={"failed-pairing": failed_pairing_memory()}), groq
    ).respond(workspace_id="workspace-a", identity=identity(), current_message="What next?")
    assert len(groq.calls) == 2
    assert result.escalation_required is True
    assert "specialist review" in result.response


@pytest.mark.asyncio
async def test_ambiguous_recommendation_retries_and_accepts_distinct_diagnostic_action():
    distinct_response = "Test the headphones with another phone or computer to see whether they disconnect there too."
    groq = FakeGroq([
        output_json(response="Try a fresh setup for the saved Bluetooth headphones."),
        output_json(response=distinct_response),
    ])
    result = await build_agent(
        FakeMemoryService(source_facts={"failed-pairing": failed_pairing_memory()}), groq
    ).respond(workspace_id="workspace-a", identity=identity(), current_message="What next?")

    assert len(groq.calls) == 2
    assert result.response == distinct_response
    assert result.escalation_required is False
    assert result.escalation_reason in (None, "")
    first_prompt = groq.calls[0]["messages"][0]["content"]
    assert "customer reported" in first_prompt
    assert "hard constraint" in first_prompt
    assert "one clearly different, low-risk troubleshooting step" in first_prompt
    assert "independent diagnostic check" in first_prompt


@pytest.mark.asyncio
@pytest.mark.parametrize("distinct_response", [
    "Test the headphones with another phone or computer to isolate whether the issue follows the headphones.",
    "Check the manufacturer's official application for an available firmware update.",
])
async def test_safe_independent_diagnostic_alternatives_are_accepted(distinct_response):
    groq = FakeGroq([output_json(response=distinct_response)])
    result = await build_agent(
        FakeMemoryService(source_facts={"failed-pairing": failed_pairing_memory()}), groq
    ).respond(workspace_id="workspace-a", identity=identity(), current_message="What next?")

    assert len(groq.calls) == 1
    assert result.response == distinct_response
    assert result.escalation_required is False


@pytest.mark.asyncio
async def test_distinct_action_validation_is_logged_without_response_content(caplog):
    caplog.set_level(logging.INFO, logger="uvicorn.error.support_action_validation")
    response_text = "Test the headphones with another phone or computer. CUSTOMER-PRIVATE-123"
    groq = FakeGroq([output_json(response=response_text)])
    result = await build_agent(
        FakeMemoryService(source_facts={"failed-pairing": failed_pairing_memory()}), groq
    ).respond(
        workspace_id="workspace-a", identity=identity(), current_message="What next?",
        correlation_id="safe-correlation-phase3",
    )

    assert result.escalation_required is False
    assert "support_action_validation outcome=accepted reason=failed_action_avoided attempt=1 correlation_id=safe-correlation-phase3" in caplog.text
    assert response_text not in caplog.text
    assert "bluetooth_forget_and_pair" not in caplog.text


@pytest.mark.asyncio
async def test_repeated_and_ambiguous_outputs_log_safe_validation_reasons(caplog):
    caplog.set_level(logging.INFO, logger="uvicorn.error.support_action_validation")
    groq = FakeGroq([
        output_json(response="Forget the Bluetooth headphones and pair them again."),
        output_json(response="Try a fresh setup for the saved Bluetooth headphones."),
    ])
    result = await build_agent(
        FakeMemoryService(source_facts={"failed-pairing": failed_pairing_memory()}), groq
    ).respond(
        workspace_id="workspace-a", identity=identity(), current_message="What next?",
        correlation_id="safe-correlation-phase3",
    )

    assert result.escalation_required is True
    assert "outcome=retry reason=failed_action_repeat attempt=1" in caplog.text
    assert "outcome=escalated reason=failed_action_uncertain attempt=2" in caplog.text
    assert "safe-correlation-phase3" in caplog.text
    assert "Forget the Bluetooth" not in caplog.text
    assert "fresh setup" not in caplog.text


@pytest.mark.asyncio
async def test_response_avoiding_failed_pairing_action_is_returned():
    safe_response = "Check whether the headphones have a firmware update available."
    groq = FakeGroq([output_json(response=safe_response)])
    result = await build_agent(
        FakeMemoryService(source_facts={"failed-pairing": failed_pairing_memory()}), groq
    ).respond(workspace_id="workspace-a", identity=identity(), current_message="What next?")
    assert result.response == safe_response
    assert result.escalation_required is False


@pytest.mark.asyncio
async def test_context_budget_instrumentation_reports_sizes_without_context_values(caplog):
    secretish_text = "PRIVATE-CUSTOMER-MESSAGE-DO-NOT-LOG"
    memory = FakeMemoryService(results=[{
        "id": "opaque-memory-id",
        "text": "PRIVATE-MEMORY-CONTENT-DO-NOT-LOG",
        "metadata": {"provenance_kind": "customer_reported", "private_value": "PRIVATE-METADATA"},
        "tags": ["customer-tag-PRIVATE"],
    }])
    groq = FakeGroq([output_json()])
    agent = build_budget_agent(memory, groq)
    with caplog.at_level(logging.INFO, logger="uvicorn.error.groq_context_size"):
        result = await agent.respond(
            workspace_id="workspace-a", identity=identity(), current_message=secretish_text,
            correlation_id="safe-correlation-1",
        )
    assert result.escalation_required is False
    line = next(record.getMessage() for record in caplog.records if "groq_context_size" in record.getMessage())
    actual_request_bytes = len(
        json.dumps(groq.calls[0], ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    )
    assert agent._estimated_request_bytes(
        groq.calls[0]["messages"][0]["content"],
        groq.calls[0]["messages"][1]["content"],
    ) == actual_request_bytes + 1024
    for field in ("system_prompt_bytes=", "user_context_bytes=", "response_schema_bytes=", "estimated_request_bytes=", "recalled_memories=1", "memory_text_bytes_by_provenance=", "memory_metadata_bytes_by_provenance=", "selected_memory_text_bytes_by_provenance=", "selected_memory_metadata_bytes_by_provenance="):
        assert field in line
    for sensitive in (secretish_text, "PRIVATE-MEMORY-CONTENT-DO-NOT-LOG", "PRIVATE-METADATA", "customer-tag-PRIVATE", "opaque-memory-id"):
        assert sensitive not in caplog.text


@pytest.mark.asyncio
@pytest.mark.parametrize("retry_case", ["validation", "failed_action"])
async def test_groq_context_measurements_are_visible_with_default_uvicorn_config(retry_case):
    logger_names = ("uvicorn", "uvicorn.error", "uvicorn.access")
    logger_snapshots = {}
    for name in logger_names:
        configured_logger = logging.getLogger(name)
        logger_snapshots[name] = (
            configured_logger.level,
            list(configured_logger.handlers),
            configured_logger.propagate,
            configured_logger.disabled,
            list(configured_logger.filters),
        )

    dictConfig(deepcopy(LOGGING_CONFIG))
    measurement_logger = logging.getLogger("uvicorn.error.groq_context_size")
    capture = CapturingHandler()
    measurement_logger.addHandler(capture)
    try:
        assert measurement_logger.getEffectiveLevel() == logging.INFO
        if retry_case == "validation":
            memory = FakeMemoryService()
            groq = FakeGroq(["malformed", output_json()])
        else:
            memory = FakeMemoryService(source_facts={"failed-pairing": failed_pairing_memory()})
            groq = FakeGroq([
                output_json(response="Remove the Bluetooth pairing and pair the device again."),
                output_json(response="Check whether a firmware update is available."),
            ])
        await build_budget_agent(memory, groq).respond(
            workspace_id="workspace-a", identity=identity(), current_message="What should I try?",
            correlation_id="safe-correlation-id",
        )
        assert len(groq.calls) == 2
        measurement_records = [
            record for record in capture.records if record.getMessage().startswith("groq_context_size ")
        ]
        assert len(measurement_records) == len(groq.calls)
        assert all(record.levelno == logging.INFO for record in measurement_records)
        assert all("correlation_id=safe-correlation-id" in record.getMessage() for record in measurement_records)
    finally:
        measurement_logger.removeHandler(capture)
        for name, snapshot in logger_snapshots.items():
            configured_logger = logging.getLogger(name)
            level, handlers, propagate, disabled, filters = snapshot
            configured_logger.setLevel(level)
            configured_logger.handlers[:] = handlers
            configured_logger.propagate = propagate
            configured_logger.disabled = disabled
            configured_logger.filters[:] = filters


@pytest.mark.asyncio
async def test_large_memory_collection_is_bounded_and_lower_priority_is_dropped():
    records = [
        {"id": f"memory-{index:03}", "text": f"Preference {index}: " + ("x" * 1200),
         "metadata": {"provenance_kind": "customer_reported"}, "tags": []}
        for index in range(12)
    ]
    groq = FakeGroq([output_json()])
    await build_budget_agent(FakeMemoryService(results=records), groq).respond(
        workspace_id="workspace-a", identity=identity(), current_message="Need help.",
    )
    context = json.loads(groq.calls[0]["messages"][1]["content"])
    assert len(context["historical_customer_memories"]) < len(records)


@pytest.mark.asyncio
async def test_exact_lower_priority_duplicates_are_deduplicated_without_losing_ids():
    duplicate = {
        "text": "Customer prefers concise steps.",
        "metadata": {"provenance_kind": "customer_reported"},
        "tags": ["provenance:customer_reported"],
    }
    memory = FakeMemoryService(results=[{"id": "memory-a", **duplicate}, {"id": "memory-b", **duplicate}])
    groq = FakeGroq([output_json(memories_used=["memory-a", "memory-b"])])
    result = await build_budget_agent(memory, groq).respond(
        workspace_id="workspace-a", identity=identity(), current_message="Help me.",
    )
    context = json.loads(groq.calls[0]["messages"][1]["content"])
    assert len(context["historical_customer_memories"]) == 1
    assert context["historical_customer_memories"][0]["duplicate_ids"] == ["memory-b"]
    assert set(result.memories_used) == {"memory-a", "memory-b"}


@pytest.mark.asyncio
async def test_mandatory_failed_attempt_survives_lower_priority_memory_pruning():
    failure = failed_pairing_memory()
    failure["metadata"]["prior_recommendation_message_id"] = "assistant-message-opaque"
    failure["metadata"]["linked_to_prior_recommendation"] = "true"
    failure["metadata"]["original_customer_statement"] = "I tried that and it failed."
    lower_priority = [
        {"id": f"lower-{index:03}", "text": "Low priority detail " + ("z" * 1200),
         "metadata": {"provenance_kind": "customer_reported"}, "tags": []}
        for index in range(10)
    ]
    groq = FakeGroq([output_json(response="Check for a firmware update.")])
    await build_budget_agent(
        FakeMemoryService(source_facts={"failed-pairing": failure}, results=lower_priority), groq
    ).respond(workspace_id="workspace-a", identity=identity(), current_message="What next?")
    request_context = json.loads(groq.calls[0]["messages"][1]["content"])
    context = request_context["conversation"]
    retained = next(item for item in context["historical_customer_memories"] if item["id"] == "failed-pairing")
    assert retained["text"] == failure["text"]
    assert retained["metadata"]["action_ids"] == "bluetooth_forget_and_pair"
    assert retained["metadata"]["prior_recommendation_message_id"] == "assistant-message-opaque"
    assert retained["metadata"]["independently_verified"] == "false"
    assert "I tried that and it failed." == retained["metadata"]["original_customer_statement"]
    assert retained["metadata"]["linked_to_prior_recommendation"] == "true"
    assert "confirmation:customer_report" in retained["tags"]
    assert "source_representations" not in retained
    assert len(context["historical_customer_memories"]) < len(lower_priority) + 1


@pytest.mark.asyncio
async def test_mandatory_failure_context_compacts_duplicate_provider_metadata():
    failure = failed_pairing_memory()
    failure["metadata"].update({
        "linked_to_prior_recommendation": "true",
        "prior_recommendation_message_id": "assistant-recommendation-id",
        "original_customer_statement": "I tried forgetting and pairing again; it failed.",
        "customer_statement_sha256": "a" * 64,
        "session_fingerprint": "b" * 64,
    })
    duplicate = {
        **failure,
        "metadata": {**failure["metadata"], "provider_extraction_note": "irrelevant " + "x" * 1800},
        "tags": [*failure["tags"], "provider:opaque " + "y" * 500],
    }
    # These are two provider representations of the same record. They are both
    # retained internally for reconciliation, but only the canonical safety fields
    # are serialized to Groq.
    groq = FakeGroq([output_json(response="Test the headphones with another device.")])
    agent = build_budget_agent(FakeMemoryService(results=[failure, duplicate]), groq)
    result = await agent.respond(
        workspace_id="workspace-a", identity=identity(), current_message="What different step?"
    )

    assert result.escalation_required is False
    assert len(groq.calls) == 1
    request_context = json.loads(groq.calls[0]["messages"][1]["content"])
    assert request_context["failed_action_constraints"] == ["bluetooth_forget_and_pair"]
    retained = request_context["conversation"]["historical_customer_memories"][0]
    assert retained["metadata"] == {
        "provenance_kind": "failed_attempt",
        "reported_outcome": "failed",
        "confirmation_source": "customer_report",
        "independently_verified": "false",
        "action_ids": "bluetooth_forget_and_pair",
        "linked_to_prior_recommendation": "true",
        "prior_recommendation_message_id": "assistant-recommendation-id",
        "original_customer_statement": "I tried forgetting and pairing again; it failed.",
    }
    assert "confirmation:customer_report" in retained["tags"]
    assert "customer_statement_sha256" not in retained["metadata"]
    assert "session_fingerprint" not in retained["metadata"]
    assert "provider_extraction_note" not in retained["metadata"]


@pytest.mark.asyncio
async def test_multiple_mandatory_failures_are_all_preserved():
    first = failed_pairing_memory()
    second = {
        "id": "failed-second",
        "text": "The customer reported that restarting the headphones did not work.",
        "metadata": {
            "provenance_kind": "failed_attempt",
            "reported_outcome": "failed",
            "confirmation_source": "customer_report",
            "independently_verified": "false",
            "action_ids": "bluetooth_forget_and_pair",
        },
        "tags": ["provenance:failed_attempt", "confirmation:customer_report"],
    }
    groq = FakeGroq([output_json(response="Check for a firmware update.")])
    await build_budget_agent(
        FakeMemoryService(results=[first, second]), groq
    ).respond(workspace_id="workspace-a", identity=identity(), current_message="What next?")
    context = json.loads(groq.calls[0]["messages"][1]["content"])["conversation"]
    assert {item["id"] for item in context["historical_customer_memories"]} == {"failed-pairing", "failed-second"}
    assert context["historical_customer_memories"][0]["metadata"]["independently_verified"] == "false"


@pytest.mark.asyncio
async def test_mandatory_context_overflow_escalates_without_calling_groq():
    failure = failed_pairing_memory()
    failure["text"] = "Exact customer-reported failure: " + ("failure details " * 700)
    groq = FakeGroq([output_json()])
    result = await build_budget_agent(
        FakeMemoryService(source_facts={"failed-pairing": failure}), groq
    ).respond(workspace_id="workspace-a", identity=identity(), current_message="What next?")
    assert result.escalation_required is True
    assert result.memory_retrieved is True
    assert not groq.calls


def ordinary_same_id_memory(text="A prior support note."):
    return {
        "id": "same-memory-id",
        "text": text,
        "metadata": {"provenance_kind": "customer_reported", "note_kind": "historical"},
        "tags": ["provenance:customer_reported"],
    }


@pytest.mark.asyncio
@pytest.mark.parametrize("mandatory_first", [False, True])
async def test_same_id_ordinary_and_mandatory_merge_keeps_mandatory_provenance(mandatory_first):
    ordinary = ordinary_same_id_memory()
    mandatory = {**failed_pairing_memory(), "id": "same-memory-id"}
    ordered = [mandatory, ordinary] if mandatory_first else [ordinary, mandatory]
    memory = FakeMemoryService(results=ordered)
    groq = FakeGroq([output_json(response="Check for a firmware update.")])
    await build_budget_agent(memory, groq).respond(
        workspace_id="workspace-a", identity=identity(), current_message="What next?"
    )
    request_context = json.loads(groq.calls[0]["messages"][1]["content"])
    context = request_context["conversation"]
    merged = context["historical_customer_memories"][0]
    assert merged["id"] == "same-memory-id"
    assert merged["metadata"]["reported_outcome"] == "failed"
    assert merged["metadata"]["action_ids"] == "bluetooth_forget_and_pair"
    assert merged["metadata"]["independently_verified"] == "false"
    assert "confirmation:customer_report" in merged["tags"]
    normalized = SupportAgent._memory_context({"results": [ordinary, mandatory]})[0]
    assert {representation["text"] for representation in normalized["source_representations"]} == {
        ordinary["text"], mandatory["text"]
    }
    assert "source_representations" not in merged
    assert request_context["failed_action_constraints"] == ["bluetooth_forget_and_pair"]


@pytest.mark.asyncio
async def test_identical_same_id_mandatory_representations_merge_without_conflict():
    mandatory = {**failed_pairing_memory(), "id": "same-memory-id"}
    memory = FakeMemoryService(results=[mandatory], source_facts={"same-memory-id": mandatory})
    groq = FakeGroq([output_json(response="Check for a firmware update.")])
    await build_budget_agent(memory, groq).respond(
        workspace_id="workspace-a", identity=identity(), current_message="What next?"
    )
    context = json.loads(groq.calls[0]["messages"][1]["content"])["conversation"]
    merged = context["historical_customer_memories"]
    assert len(merged) == 1
    assert merged[0]["metadata"]["independently_verified"] == "false"
    assert merged[0]["metadata"]["action_ids"] == "bluetooth_forget_and_pair"


@pytest.mark.asyncio
async def test_conflicting_same_id_mandatory_provenance_escalates_without_groq():
    customer_report = {**failed_pairing_memory(), "id": "same-memory-id"}
    independently_verified = {**customer_report, "metadata": {
        **customer_report["metadata"], "independently_verified": "true"
    }}
    groq = FakeGroq([output_json()])
    result = await build_budget_agent(
        FakeMemoryService(results=[customer_report, independently_verified]), groq
    ).respond(workspace_id="workspace-a", identity=identity(), current_message="What next?")
    assert result.escalation_required is True
    assert "provenance" in result.escalation_reason
    assert not groq.calls


@pytest.mark.asyncio
async def test_same_id_ordinary_duplicates_do_not_become_mandatory():
    first = ordinary_same_id_memory("A prior note about the product.")
    second = ordinary_same_id_memory("A second historical note about the product.")
    groq = FakeGroq([output_json()])
    await build_budget_agent(
        FakeMemoryService(results=[first, second]), groq
    ).respond(workspace_id="workspace-a", identity=identity(), current_message="Help me.")
    context = json.loads(groq.calls[0]["messages"][1]["content"])
    memory = context["historical_customer_memories"][0]
    assert memory["provenance"] == "customer_reported"
    assert "failed_action_constraints" not in context
    assert memory.get("safety_conflict") is False


@pytest.mark.asyncio
async def test_same_id_mandatory_record_survives_budget_selection():
    ordinary = ordinary_same_id_memory()
    mandatory = {**failed_pairing_memory(), "id": "same-memory-id"}
    lower_priority = [
        {"id": f"low-{index:02}", "text": "Unneeded detail " + ("x" * 1200),
         "metadata": {"provenance_kind": "customer_reported"}, "tags": []}
        for index in range(10)
    ]
    groq = FakeGroq([output_json(response="Check for a firmware update.")])
    await build_budget_agent(
        FakeMemoryService(results=[ordinary, *lower_priority], source_facts={"same-memory-id": mandatory}), groq
    ).respond(workspace_id="workspace-a", identity=identity(), current_message="What next?")
    context = json.loads(groq.calls[0]["messages"][1]["content"])["conversation"]
    merged = next(item for item in context["historical_customer_memories"] if item["id"] == "same-memory-id")
    assert merged["text"] == mandatory["text"]
    assert merged["metadata"]["action_ids"] == "bluetooth_forget_and_pair"
    assert merged["metadata"]["independently_verified"] == "false"
    assert len(context["historical_customer_memories"]) < len(lower_priority) + 1


@pytest.mark.asyncio
async def test_ambiguous_equivalent_advice_is_escalated_not_claimed_as_avoided():
    groq = FakeGroq([
        output_json(response="Try a fresh setup for the saved Bluetooth headphones."),
        output_json(response="Remove the Bluetooth entry and begin pairing from the start."),
    ])
    result = await build_agent(
        FakeMemoryService(source_facts={"failed-pairing": failed_pairing_memory()}), groq
    ).respond(workspace_id="workspace-a", identity=identity(), current_message="What next?")
    assert len(groq.calls) == 2
    assert result.escalation_required is True
    assert "specialist review" in result.response


@pytest.mark.asyncio
async def test_failed_action_correction_prompt_requests_a_distinct_concrete_alternative():
    groq = FakeGroq([
        output_json(response="Try a fresh setup for the saved Bluetooth headphones."),
        output_json(response="Test the headphones with another device.")
    ])
    await build_agent(
        FakeMemoryService(source_facts={"failed-pairing": failed_pairing_memory()}), groq
    ).respond(workspace_id="workspace-a", identity=identity(), current_message="What next?")

    correction_prompt = groq.calls[1]["messages"][0]["content"]
    assert "one specific, low-risk action" in correction_prompt
    assert "clearly different in method" in correction_prompt
    assert "Do not merely rephrase" in correction_prompt


def test_async_groq_client_gets_configured_bounded_timeout(monkeypatch):
    import app.agents.support_agent as support_agent_module

    captured = {}

    class StubGroq:
        def __init__(self, **kwargs):
            captured.update(kwargs)

    monkeypatch.setattr(support_agent_module, "AsyncGroq", StubGroq)
    settings = Settings(groq_api_key="fake-key", groq_timeout_seconds=24, _env_file=None)
    SupportAgent(settings=settings, memory_service=FakeMemoryService())
    assert captured["timeout"] == 24


@pytest.mark.asyncio
async def test_frustration_is_acknowledged_and_prompt_requires_empathy() -> None:
    memory = FakeMemoryService()
    groq = FakeGroq([output_json(response="I’m sorry this has been so frustrating. I’ll help you work through it.")])
    result = await build_agent(memory, groq).respond(
        workspace_id="workspace-a",
        identity=identity(),
        current_message="I've explained this twice already. This is really frustrating.",
    )
    assert "frustrating" in result.response.lower()
    assert "acknowledge frustration" in groq.calls[0]["messages"][0]["content"].lower()


@pytest.mark.asyncio
async def test_missing_memories_are_handled_as_no_history() -> None:
    memory = FakeMemoryService(results=[])
    groq = FakeGroq([output_json(memories_used=["invented-id"], memory_retrieved=True)])
    result = await build_agent(memory, groq).respond(
        workspace_id="workspace-a", identity=identity(), current_message="I need help."
    )
    context = json.loads(groq.calls[0]["messages"][1]["content"])
    assert context["historical_customer_memories"] == []
    assert result.memories_used == []
    assert result.memory_retrieved is False


@pytest.mark.asyncio
async def test_recall_failure_stops_generation_and_propagates_controlled_error() -> None:
    timeline = []
    memory = FakeMemoryService(error=MemoryRetrievalError(), timeline=timeline)
    groq = FakeGroq([output_json()], timeline=timeline)
    with pytest.raises(MemoryRetrievalError):
        await build_agent(memory, groq).respond(
            workspace_id="workspace-a", identity=identity(), current_message="Where are we?"
        )
    assert timeline == ["recall"]


@pytest.mark.asyncio
async def test_groq_failure_becomes_controlled_error() -> None:
    agent = build_agent(FakeMemoryService(), FakeGroq(error=RuntimeError("sensitive provider detail")))
    with pytest.raises(GroqGenerationError) as error:
        await agent.respond(workspace_id="workspace-a", identity=identity(), current_message="Help")
    assert "sensitive provider detail" not in str(error.value)


@pytest.mark.asyncio
async def test_groq_timeout_becomes_controlled_error():
    groq = FakeGroq(error=TimeoutError("provider timeout"))
    with pytest.raises(GroqGenerationError) as error:
        await build_agent(FakeMemoryService(), groq).respond(
            workspace_id="workspace-a", identity=identity(), current_message="Help"
        )
    assert "provider timeout" not in str(error.value)


def provider_status_error(error_type, status_code):
    request = httpx.Request("POST", "https://api.groq.com/openai/v1/chat/completions")
    response = httpx.Response(status_code, request=request)
    return error_type(
        "sensitive provider message with customer@example.test and secret-value",
        response=response,
        body={"error": {"message": "sensitive response body and bearer-token-value"}},
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("status_code", "error_type", "exception_name"),
    [
        (400, BadRequestError, "BadRequestError"),
        (401, AuthenticationError, "AuthenticationError"),
        (429, RateLimitError, "RateLimitError"),
        (503, InternalServerError, "InternalServerError"),
    ],
)
async def test_groq_status_failure_logs_only_class_status_and_correlation(
    caplog, status_code, error_type, exception_name
):
    sensitive_error = provider_status_error(error_type, status_code)
    groq = FakeGroq(error=sensitive_error)
    correlation_id = "safe-correlation-123"
    caplog.set_level(logging.WARNING, logger="app.agents.support_agent")
    with pytest.raises(GroqGenerationError) as raised:
        await build_agent(FakeMemoryService(), groq).respond(
            workspace_id="workspace-a",
            identity=identity(),
            current_message="Help",
            correlation_id=correlation_id,
        )

    assert raised.value.__suppress_context__ is True
    assert raised.value.status_code == 503
    assert raised.value.public_message == "The support agent is temporarily unavailable"
    assert len(caplog.records) == 1
    message = caplog.records[0].getMessage()
    assert message == (
        f"groq_generation_failed exception_class={exception_name} "
        f"status={status_code} correlation_id={correlation_id}"
    )
    for secret_fragment in (
        "sensitive provider message",
        "customer@example.test",
        "secret-value",
        "sensitive response body",
        "bearer-token-value",
    ):
        assert secret_fragment not in caplog.text


@pytest.mark.asyncio
@pytest.mark.parametrize("error_type", [APIConnectionError, APITimeoutError])
async def test_groq_connection_and_timeout_failures_log_unavailable_status_without_details(
    caplog, error_type
):
    request = httpx.Request("POST", "https://api.groq.com/openai/v1/chat/completions")
    error = error_type(request=request)
    groq = FakeGroq(error=error)
    caplog.set_level(logging.WARNING, logger="app.agents.support_agent")
    with pytest.raises(GroqGenerationError):
        await build_agent(FakeMemoryService(), groq).respond(
            workspace_id="workspace-a",
            identity=identity(),
            current_message="Help",
            correlation_id="safe-correlation-456",
        )
    assert len(caplog.records) == 1
    message = caplog.records[0].getMessage()
    assert f"exception_class={error_type.__name__}" in message
    assert "status=unavailable" in message
    assert "correlation_id=safe-correlation-456" in message
    assert "api.groq.com" not in caplog.text


@pytest.mark.asyncio
async def test_malformed_structured_output_is_retried_once_then_validated() -> None:
    groq = FakeGroq(["not json", output_json()])
    result = await build_agent(FakeMemoryService(), groq).respond(
        workspace_id="workspace-a", identity=identity(), current_message="Help"
    )
    assert len(groq.calls) == 2
    assert "failed validation" in groq.calls[1]["messages"][0]["content"]
    assert result.response


@pytest.mark.asyncio
async def test_malformed_output_after_retry_is_rejected() -> None:
    groq = FakeGroq(["not json", "still not json"])
    with pytest.raises(InvalidAgentOutputError):
        await build_agent(FakeMemoryService(), groq).respond(
            workspace_id="workspace-a", identity=identity(), current_message="Help"
        )
    assert len(groq.calls) == 2


@pytest.mark.asyncio
@pytest.mark.parametrize("unsafe_claim", ["Your issue is resolved now.", "It's fixed now.", "I fixed it."])
async def test_unconfirmed_resolution_claim_is_retried_and_never_returned(unsafe_claim: str) -> None:
    groq = FakeGroq([
        output_json(response=unsafe_claim),
        output_json(response="I can’t confirm it is resolved yet. What do you see now?"),
    ])
    result = await build_agent(FakeMemoryService(), groq).respond(
        workspace_id="workspace-a", identity=identity(), current_message="It still doesn't work."
    )
    assert len(groq.calls) == 2
    assert unsafe_claim not in result.response


@pytest.mark.asyncio
async def test_resolution_claim_is_rejected_if_retry_still_claims_resolution() -> None:
    groq = FakeGroq([output_json(response="Your issue is resolved."), output_json(response="You're all set.")])
    with pytest.raises(InvalidAgentOutputError):
        await build_agent(FakeMemoryService(), groq).respond(
            workspace_id="workspace-a", identity=identity(), current_message="The issue is not fixed."
        )


@pytest.mark.asyncio
async def test_customer_and_visitor_memory_namespaces_are_isolated() -> None:
    workspace = "workspace-a"
    subject_id = str(uuid4())
    memory = FakeMemoryService()
    groq = FakeGroq([output_json(), output_json()])
    agent = build_agent(memory, groq)
    await agent.respond(
        workspace_id=workspace,
        identity=identity("customer", subject_id, workspace),
        current_message="Customer message",
    )
    await agent.respond(
        workspace_id=workspace,
        identity=identity("visitor", subject_id, workspace),
        current_message="Visitor message",
    )
    assert memory.calls[0][1:] == (subject_id, "customer", "Customer message")
    assert memory.calls[1][1:] == (subject_id, "visitor", "Visitor message")


@pytest.mark.asyncio
async def test_workspace_mismatch_is_rejected_before_memory_access() -> None:
    memory = FakeMemoryService()
    with pytest.raises(ValueError):
        await build_agent(memory, FakeGroq()).respond(
            workspace_id="workspace-b",
            identity=identity("customer", workspace="workspace-a"),
            current_message="Help",
        )
    assert memory.calls == []
