import hashlib
import logging
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import uuid4

import jwt
import pytest
from fastapi.testclient import TestClient

from app.agents.support_agent import SupportAgent
from app.core.config import Settings
from app.core.security import VerifiedIdentity
from app.main import create_app
from app import main as app_main
from app.memory.memory_service import MemoryRetrievalError, MemoryRetentionError
from app.schemas.agent import SupportAgentOutput
from app.services.chat_workflow import ChatWorkflow

IDENTITY_SECRET = "test-identity-secret-that-is-long-enough-000001"
WORKSPACE_INTERNAL = str(uuid4())
WORKSPACE_PUBLIC = str(uuid4())
CUSTOMER_ID = str(uuid4())
VISITOR_ID = str(uuid4())


def token(identity_type: str, subject_id: str) -> str:
    claim = "customer_id" if identity_type == "customer" else "visitor_id"
    return jwt.encode(
        {
            "exp": datetime.now(timezone.utc) + timedelta(minutes=5),
            "iat": datetime.now(timezone.utc),
            "iss": "recall-test-issuer",
            "aud": "recall-test-audience",
            "workspace_id": WORKSPACE_INTERNAL,
            "identity_type": identity_type,
            claim: subject_id,
        },
        IDENTITY_SECRET,
        algorithm="HS256",
    )


def request_body(identity_type="customer", *, session="session-1", message="The issue continues"):
    body = {"session_id": session, "message": message, "identity_token": token(
        identity_type, CUSTOMER_ID if identity_type == "customer" else VISITOR_ID
    )}
    body["customer_id" if identity_type == "customer" else "visitor_id"] = (
        CUSTOMER_ID if identity_type == "customer" else VISITOR_ID
    )
    return body


def agent_output(**overrides):
    result = {
        "response": "I understand this is frustrating. Let’s continue with a different check.",
        "sentiment": "frustrated",
        "memories_used": ["memory-1"],
        "memory_retrieved": True,
        "escalation_required": False,
        "escalation_reason": "",
        "interaction_summary": "The customer reports the issue continues.",
        "suggested_memory_facts": ["The customer reports the issue continues."],
    }
    result.update(overrides)
    return SupportAgentOutput.model_validate(result)


class FakeRepository:
    def __init__(self, *, new_conversation=True, error=None, escalation_created=True, escalation_error=False, identity_verified=True, timeline=None, prior_assistant=None) -> None:
        self.new_conversation = new_conversation
        self.error = error
        self.escalation_created = escalation_created
        self.escalation_error = escalation_error
        self.identity_verified = identity_verified
        self.timeline = timeline if timeline is not None else []
        self.calls = []
        self.idempotent_messages = {}
        self.prior_assistant = prior_assistant
        self.conversation = {
            "id": str(uuid4()),
            "workspace_id": WORKSPACE_INTERNAL,
            "customer_id": CUSTOMER_ID,
            "visitor_id": None,
            "session_id": "session-1",
            "status": "open",
        }

    async def resolve_workspace(self, public_id):
        self.calls.append(("workspace", public_id))
        self.timeline.append("workspace")
        if self.error == "workspace":
            from app.database.chat_repository import ChatRepositoryError
            raise ChatRepositoryError()
        if self.error == "workspace_not_found":
            from app.database.chat_repository import WorkspaceNotFoundError
            raise WorkspaceNotFoundError()
        assert public_id == WORKSPACE_PUBLIC
        return {"id": WORKSPACE_INTERNAL, "public_id": WORKSPACE_PUBLIC}

    async def resolve_customer(self, workspace_id, customer_id):
        self.calls.append(("customer", workspace_id, customer_id))
        self.timeline.append("customer")
        if self.error == "customer":
            from app.database.chat_repository import CustomerNotFoundError
            raise CustomerNotFoundError()
        assert workspace_id == WORKSPACE_INTERNAL
        assert customer_id == CUSTOMER_ID
        return {"id": CUSTOMER_ID, "workspace_id": WORKSPACE_INTERNAL, "identity_verified": self.identity_verified}

    async def get_or_create_conversation(self, *, workspace_id, identity, session_id):
        self.timeline.append("conversation")
        self.calls.append(("conversation", workspace_id, identity, session_id))
        self.conversation.update({
            "workspace_id": workspace_id,
            "customer_id": identity.subject_id if identity.identity_type == "customer" else None,
            "visitor_id": identity.subject_id if identity.identity_type == "visitor" else None,
            "session_id": session_id,
        })
        return self.conversation, self.new_conversation

    async def insert_message(self, *, role, content, **kwargs):
        self.timeline.append(f"message:{role}")
        self.calls.append(("message", role, content, kwargs))
        metadata = kwargs.get("metadata", {})
        row = {"id": str(uuid4()), "role": role, "content": content, "metadata": metadata,
               "created_at": datetime.now(timezone.utc).isoformat()}
        if metadata.get("idempotency_key"):
            self.idempotent_messages[(role, metadata["idempotency_key"])] = row
        return row

    async def find_idempotent_message(self, *, role, idempotency_key, **kwargs):
        self.calls.append(("idempotent_lookup", role, idempotency_key))
        return self.idempotent_messages.get((role, idempotency_key))

    async def find_prior_assistant_message(self, **kwargs):
        self.calls.append(("prior_assistant", kwargs))
        return self.prior_assistant

    async def update_conversation(self, **kwargs):
        self.timeline.append("update_conversation")
        self.calls.append(("update_conversation", kwargs))

    async def update_customer_interaction(self, **kwargs):
        self.timeline.append("update_customer")
        self.calls.append(("update_customer", kwargs))

    async def update_message_metadata(self, **kwargs):
        self.calls.append(("message_metadata", kwargs))
        for row in self.idempotent_messages.values():
            if row["id"] == kwargs["message_id"]:
                row["metadata"] = kwargs["metadata"]

    async def record_activity(self, *, event_type, **kwargs):
        self.timeline.append(f"activity:{event_type}")
        self.calls.append(("activity", event_type, kwargs))

    async def create_escalation_ticket(self, **kwargs):
        self.timeline.append("ticket")
        self.calls.append(("ticket", kwargs))
        if self.escalation_error:
            from app.database.chat_repository import ChatRepositoryError
            raise ChatRepositoryError()
        return self.escalation_created


class FakeMemoryService:
    def __init__(self, *, error=None, timeline=None) -> None:
        self.error = error
        self.timeline = timeline if timeline is not None else []
        self.calls = []

    async def retain_memory(self, workspace_id, subject_id, content, **kwargs):
        self.timeline.append("retain")
        self.calls.append((workspace_id, subject_id, content, kwargs))
        if self.error:
            raise self.error
        return {"ok": True}


class FakeAgent:
    def __init__(self, *, output=None, error=None, timeline=None) -> None:
        self.output = output or agent_output()
        self.error = error
        self.timeline = timeline if timeline is not None else []
        self.calls = []

    async def respond(self, **kwargs):
        self.timeline.append("generate")
        self.calls.append(kwargs)
        if self.error:
            raise self.error
        return self.output


def make_workflow(*, repository=None, memory=None, agent=None, new_conversation=True, output=None):
    repository = repository or FakeRepository(new_conversation=new_conversation)
    memory = memory or FakeMemoryService()
    agent = agent or FakeAgent(output=output)
    settings = Settings(identity_token_secret=IDENTITY_SECRET, identity_token_issuer="recall-test-issuer",
                        identity_token_audience="recall-test-audience", _env_file=None)
    return ChatWorkflow(repository=repository, memory_service=memory, support_agent=agent, settings=settings), repository, memory, agent


def post_chat(workflow, body):
    app = create_app()
    with TestClient(app) as client:
        app.state.chat_workflow = workflow
    return client.post(
            "/api/v1/chat",
            headers={"X-Workspace-ID": WORKSPACE_PUBLIC, "Idempotency-Key": "test-idempotency-key-001"},
            json=body,
        )


def test_successful_customer_chat_persists_messages_updates_and_retains_after_generation():
    timeline = []
    repository = FakeRepository(timeline=timeline)
    memory = FakeMemoryService(timeline=timeline)
    agent = FakeAgent(timeline=timeline)
    workflow, _, _, _ = make_workflow(repository=repository, memory=memory, agent=agent)
    response = post_chat(workflow, request_body())
    assert response.status_code == 200
    assert response.headers["X-Workflow-Status"] == "complete"
    assert response.headers["X-Memory-Status"] == "stored"
    assert response.json() == {
        "response": agent.output.response,
        "session_id": "session-1",
        "sentiment": "frustrated",
        "memories_used": ["memory-1"],
        "memory_retrieved": True,
        "escalation_required": False,
        "escalation_reason": None,
    }
    assert timeline.index("message:customer") < timeline.index("generate")
    assert timeline.index("generate") < timeline.index("message:assistant") < timeline.index("retain")
    assert memory.calls[0][1] == CUSTOMER_ID
    assert len(memory.calls) == 3
    assert memory.calls[0][3]["metadata"]["provenance_kind"] == "customer_reported"
    assert memory.calls[1][3]["metadata"]["provenance_kind"] == "assistant_generated"
    assert memory.calls[2][3]["metadata"]["provenance_kind"] == "model_suggestion"
    assert "suggestions:unverified" in memory.calls[2][3]["tags"]
    assert any(call[0] == "update_conversation" for call in repository.calls)
    assert any(call[0] == "update_customer" for call in repository.calls)


def test_customer_reported_failure_is_linked_to_prior_assistant_recommendation(caplog):
    caplog.set_level(logging.INFO, logger="uvicorn.error.memory_provenance")
    failed_message = (
        "I followed your suggestion to forget these headphones and pair them again. "
        "It did not help; they still disconnect."
    )
    repository = FakeRepository(prior_assistant={
        "id": str(uuid4()), "workspace_id": WORKSPACE_INTERNAL,
        "conversation_id": "conversation", "role": "assistant",
        "content": "Try forgetting these headphones in Bluetooth settings and pairing them again.",
    })
    workflow, _, memory, agent = make_workflow(repository=repository)
    response = post_chat(workflow, request_body(message=failed_message))
    assert response.status_code == 200

    reported_failure = next(
        call for call in memory.calls
        if call[3]["metadata"].get("provenance_kind") == "failed_attempt"
    )
    metadata = reported_failure[3]["metadata"]
    assert metadata["confirmation_source"] == "customer_report"
    assert metadata["independently_verified"] == "false"
    assert metadata["reported_outcome"] == "failed"
    assert "provenance:failed_attempt" in reported_failure[3]["tags"]
    assert "confirmation:customer_report" in reported_failure[3]["tags"]
    assert metadata["session_fingerprint"] == hashlib.sha256(b"session-1").hexdigest()
    assert metadata["action_ids"] == "bluetooth_forget_and_pair"
    assert metadata["linked_to_prior_recommendation"] == "true"
    assert metadata["prior_recommendation_message_id"] == repository.prior_assistant["id"]
    assert metadata["customer_statement_sha256"] == hashlib.sha256(failed_message.encode("utf-8")).hexdigest()
    assert reported_failure[2] == failed_message
    assert agent.calls[0]["reported_failed_action_ids"] == {"bluetooth_forget_and_pair"}
    assert "failed_attempt_provenance outcome=linked" in caplog.text
    assert "failed_attempt_provenance outcome=retention_success" in caplog.text
    assert failed_message not in caplog.text


def test_exact_sarah_phase_two_report_links_to_phase_one_repair_recommendation():
    phase_one_response = (
        "Please forget these headphones in Bluetooth settings and re-pair them."
    )
    phase_two_message = (
        "I followed your suggestion to forget these headphones in Bluetooth settings and pair them again. "
        "It did not help; they still disconnect after about 10 minutes."
    )
    prior_assistant = {
        "id": str(uuid4()), "workspace_id": WORKSPACE_INTERNAL,
        "conversation_id": "conversation", "role": "assistant",
        "content": phase_one_response,
    }
    repository = FakeRepository(prior_assistant=prior_assistant)
    workflow, _, memory, _ = make_workflow(repository=repository)

    response = post_chat(workflow, request_body(message=phase_two_message))

    assert response.status_code == 200
    failed_attempt = next(
        call for call in memory.calls
        if call[3]["metadata"].get("provenance_kind") == "failed_attempt"
    )
    assert failed_attempt[2] == phase_two_message
    assert failed_attempt[3]["metadata"]["action_ids"] == "bluetooth_forget_and_pair"
    assert failed_attempt[3]["metadata"]["prior_recommendation_message_id"] == prior_assistant["id"]
    assert failed_attempt[3]["metadata"]["session_fingerprint"] == hashlib.sha256(b"session-1").hexdigest()
    assert failed_attempt[3]["metadata"]["customer_statement_sha256"] == hashlib.sha256(
        phase_two_message.encode("utf-8")
    ).hexdigest()
    assert failed_attempt[3]["tags"] == [
        "provenance:failed_attempt", "outcome:reported_failed", "confirmation:customer_report",
        "identity:customer",
    ]


def test_multistep_phase_one_response_links_phase_two_report():
    phase_one_response = (
        "Find the headphones in Bluetooth settings. Select ‘Forget’ or ‘Remove’ the device. "
        "Turn Bluetooth off and on. Put the headphones into pairing mode. Pair them again."
    )
    phase_two_message = (
        "I followed your suggestion to forget these headphones and pair them again. "
        "It did not help; they still disconnect."
    )
    repository = FakeRepository(prior_assistant={
        "id": str(uuid4()), "workspace_id": WORKSPACE_INTERNAL,
        "conversation_id": "conversation", "role": "assistant", "content": phase_one_response,
    })
    workflow, _, memory, _ = make_workflow(repository=repository)

    response = post_chat(workflow, request_body(message=phase_two_message))

    assert response.status_code == 200
    failed_attempt = next(
        call for call in memory.calls
        if call[3]["metadata"].get("provenance_kind") == "failed_attempt"
    )
    assert failed_attempt[3]["metadata"]["action_ids"] == "bluetooth_forget_and_pair"
    assert failed_attempt[3]["metadata"]["prior_recommendation_message_id"] == repository.prior_assistant["id"]


def test_phase_two_pairing_failure_is_not_linked_to_a_distinct_phase_one_recommendation(caplog):
    caplog.set_level(logging.INFO, logger="uvicorn.error.memory_provenance")
    prior_assistant = {
        "id": str(uuid4()), "workspace_id": WORKSPACE_INTERNAL,
        "conversation_id": "conversation", "role": "assistant",
        "content": "Test the headphones with another device to see whether they disconnect there too.",
    }
    workflow, _, memory, _ = make_workflow(repository=FakeRepository(prior_assistant=prior_assistant))
    phase_two_message = (
        "I followed your suggestion to forget these headphones in Bluetooth settings and pair them again. "
        "It did not help; they still disconnect after about 10 minutes."
    )

    response = post_chat(workflow, request_body(message=phase_two_message))

    assert response.status_code == 200
    assert not any(
        call[3]["metadata"].get("provenance_kind") == "failed_attempt"
        for call in memory.calls
    )
    assert "failed_attempt_provenance outcome=creation_skipped reason=prior_recommendation_action_mismatch" in caplog.text


def test_failure_record_creation_skip_is_logged_without_customer_data(caplog):
    caplog.set_level(logging.INFO, logger="uvicorn.error.memory_provenance")
    message = (
        "I followed your suggestion to forget these headphones in Bluetooth settings and pair them again. "
        "It did not help; they still disconnect after about 10 minutes."
    )
    workflow, _, memory, _ = make_workflow(repository=FakeRepository(prior_assistant=None))

    response = post_chat(workflow, request_body(message=message))

    assert response.status_code == 200
    assert not any(call[3]["metadata"].get("provenance_kind") == "failed_attempt" for call in memory.calls)
    assert "failed_attempt_provenance outcome=creation_skipped reason=prior_recommendation_not_found" in caplog.text
    assert message not in caplog.text


def test_failed_attempt_retention_failure_is_distinguished_in_logs(caplog):
    from app.memory.memory_service import MemoryRetentionError

    caplog.set_level(logging.INFO, logger="uvicorn.error.memory_provenance")

    class FailOnlyFailedAttempt(FakeMemoryService):
        async def retain_memory(self, workspace_id, subject_id, content, **kwargs):
            self.calls.append((workspace_id, subject_id, content, kwargs))
            if (kwargs.get("metadata") or {}).get("provenance_kind") == "failed_attempt":
                raise MemoryRetentionError()
            return {"ok": True}

    prior_assistant = {
        "id": str(uuid4()), "workspace_id": WORKSPACE_INTERNAL,
        "conversation_id": "conversation", "role": "assistant",
        "content": "Please forget these headphones in Bluetooth settings and pair them again.",
    }
    repository = FakeRepository(prior_assistant=prior_assistant)
    memory = FailOnlyFailedAttempt()
    workflow, _, _, _ = make_workflow(repository=repository, memory=memory)
    message = "I followed your suggestion to forget these headphones and pair them again. It did not help."

    response = post_chat(workflow, request_body(message=message))

    assert response.status_code == 200
    assert response.headers["X-Workflow-Status"] == "retention_failed"
    assert response.headers["X-Memory-Status"] == "failed"
    assert "failed_attempt_provenance outcome=retention_failure" in caplog.text
    assert message not in caplog.text


def test_unrelated_failed_action_is_not_attributed_to_prior_pairing_recommendation():
    repository = FakeRepository(prior_assistant={
        "id": str(uuid4()), "workspace_id": WORKSPACE_INTERNAL,
        "conversation_id": "conversation", "role": "assistant",
        "content": "Try forgetting these headphones in Bluetooth settings and pairing them again.",
    })
    workflow, _, memory, _ = make_workflow(repository=repository)
    message = "I followed your suggestion to update the firmware, but that did not help."
    assert post_chat(workflow, request_body(message=message)).status_code == 200
    assert not any(call[3]["metadata"].get("provenance_kind") == "failed_attempt" for call in memory.calls)
    customer_record = next(call for call in memory.calls if call[3]["metadata"].get("provenance_kind") == "customer_reported")
    assert customer_record[2] == message


def test_contrast_clause_failure_is_not_attributed_to_pairing_recommendation():
    repository = FakeRepository(prior_assistant={
        "id": str(uuid4()), "workspace_id": WORKSPACE_INTERNAL,
        "conversation_id": "conversation", "role": "assistant",
        "content": "Try forgetting the Bluetooth headphones and pairing them again.",
    })
    workflow, _, memory, _ = make_workflow(repository=repository)
    message = (
        "I followed your suggestion to forget these headphones and pair them again, "
        "but updating the firmware did not help."
    )
    assert post_chat(workflow, request_body(message=message)).status_code == 200
    assert not any(call[3]["metadata"].get("provenance_kind") == "failed_attempt" for call in memory.calls)


def test_ambiguous_failure_phrase_is_retained_only_as_customer_reported():
    workflow, _, memory, _ = make_workflow()
    message = "That didn't work."
    assert post_chat(workflow, request_body(message=message)).status_code == 200
    assert not any(call[3]["metadata"].get("provenance_kind") == "failed_attempt" for call in memory.calls)
    customer_record = next(call for call in memory.calls if call[3]["metadata"].get("provenance_kind") == "customer_reported")
    assert customer_record[2] == message


def test_idempotent_retry_reuses_saved_response_without_duplicate_messages_or_generation():
    workflow, repository, _, agent = make_workflow()
    body = request_body()
    first = post_chat(workflow, body)
    second = post_chat(workflow, body)
    assert first.status_code == second.status_code == 200
    assert first.json() == second.json()
    assert len([call for call in repository.calls if call[0] == "message"]) == 2
    assert len(agent.calls) == 1


def test_reusing_idempotency_key_for_different_message_is_rejected():
    workflow, _, _, _ = make_workflow()
    assert post_chat(workflow, request_body()).status_code == 200
    response = post_chat(workflow, request_body(message="A different request"))
    assert response.status_code == 409


def test_unverified_customer_record_cannot_authenticate_signed_request():
    repository = FakeRepository(identity_verified=False)
    workflow, _, _, _ = make_workflow(repository=repository)
    response = post_chat(workflow, request_body())
    assert response.status_code == 404
    assert not any(call[0] == "conversation" for call in repository.calls)


def test_visitor_chat_uses_verified_visitor_scope_without_customer_lookup():
    workflow, repository, memory, agent = make_workflow()
    response = post_chat(workflow, request_body("visitor"))
    assert response.status_code == 200
    assert not any(call[0] == "customer" for call in repository.calls)
    conversation_call = next(call for call in repository.calls if call[0] == "conversation")
    assert conversation_call[2].identity_type == "visitor"
    assert conversation_call[2].subject_id == VISITOR_ID
    assert memory.calls[0][1] == VISITOR_ID
    assert memory.calls[0][3]["subject_type"] == "visitor"
    assert agent.calls[0]["identity"].identity_type == "visitor"


def test_existing_conversation_is_reused():
    workflow, repository, _, _ = make_workflow(new_conversation=False)
    response = post_chat(workflow, request_body(session="existing-session"))
    assert response.status_code == 200
    assert repository.calls[1][0] == "customer"
    assert repository.calls[2][0] == "conversation"
    assert repository.calls[2][3] == "existing-session"
    customer_event = next(call for call in repository.calls if call[:2] == ("activity", "customer_message_received"))
    assert customer_event[2]["metadata"]["new_conversation"] is False


def test_retention_failure_preserves_successful_response_and_records_failure():
    repository = FakeRepository()
    memory = FakeMemoryService(error=MemoryRetentionError())
    workflow, _, _, agent = make_workflow(repository=repository, memory=memory)
    response = post_chat(workflow, request_body())
    assert response.status_code == 200
    assert response.headers["X-Workflow-Status"] == "retention_failed"
    assert response.headers["X-Memory-Status"] == "failed"
    assert response.json()["response"] == agent.output.response
    assert "memory_updated" not in response.json()
    assert any(call[:2] == ("activity", "memory_retention_failed") for call in repository.calls)
    assert any(
        call[0] == "message_metadata" and call[1]["metadata"]["retention_status"] == "failed"
        for call in repository.calls
    )


def test_escalation_creates_ticket_and_activity():
    repository = FakeRepository()
    workflow, _, _, _ = make_workflow(
        repository=repository,
        output=agent_output(escalation_required=True, escalation_reason="Customer requests a human agent."),
    )
    response = post_chat(workflow, request_body())
    assert response.status_code == 200
    assert response.json()["escalation_required"] is True
    assert any(call[0] == "ticket" for call in repository.calls)
    assert any(call[:2] == ("activity", "escalation_recommended") for call in repository.calls)


def test_escalation_failure_returns_persisted_response_as_partial_not_failed_chat():
    repository = FakeRepository(escalation_error=True)
    workflow, _, _, _ = make_workflow(
        repository=repository,
        output=agent_output(escalation_required=True, escalation_reason="A person should follow up."),
    )
    response = post_chat(
        workflow,
        request_body(),
    )
    # The route marks this as HTTP 202 with an escalation-pending header when a Response is provided.
    # TestClient route supplies the response object; the saved answer remains available.
    assert response.status_code == 202
    assert response.headers["X-Workflow-Status"] == "escalation_pending"
    assert response.headers["X-Memory-Status"] == "stored"
    assert response.json()["response"]


def test_invalid_identity_does_not_resolve_customer_or_create_messages():
    workflow, repository, _, _ = make_workflow()
    body = request_body()
    body["identity_token"] = token("visitor", VISITOR_ID)
    response = post_chat(workflow, body)
    assert response.status_code == 401
    assert not any(call[0] == "customer" for call in repository.calls)
    assert not any(call[0] == "message" for call in repository.calls)


def test_workspace_header_must_be_uuid():
    workflow, _, _, _ = make_workflow()
    app = create_app()
    with TestClient(app) as client:
        app.state.chat_workflow = workflow
        response = client.post(
            "/api/v1/chat", headers={"X-Workspace-ID": "not-a-uuid", "Idempotency-Key": "test-idempotency-key-001"}, json=request_body()
        )
    assert response.status_code == 400


def test_cors_allows_idempotency_key_and_exposes_workflow_headers(monkeypatch):
    monkeypatch.setattr(
        app_main,
        "get_settings",
        lambda: Settings(frontend_url="http://localhost:5173", _env_file=None),
    )
    app = create_app()
    with TestClient(app) as client:
        response = client.options(
            "/api/v1/chat",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type,idempotency-key,x-workspace-id",
            },
        )
        actual_response = client.get("/health", headers={"Origin": "http://localhost:5173"})
    assert response.status_code == 200
    assert "idempotency-key" in response.headers["access-control-allow-headers"].lower()
    exposed = actual_response.headers["access-control-expose-headers"].lower()
    assert "x-workflow-status" in exposed
    assert "x-memory-status" in exposed


@pytest.mark.parametrize(
    "identity_fields",
    [{}, {"customer_id": CUSTOMER_ID, "visitor_id": VISITOR_ID}],
)
def test_request_requires_exactly_one_identity_type(identity_fields):
    workflow, _, _, _ = make_workflow()
    body = {"session_id": "session-1", "message": "Help", **identity_fields}
    response = post_chat(workflow, body)
    assert response.status_code == 400


def test_supabase_failure_is_controlled():
    from app.database.chat_repository import ChatRepositoryError

    repository = FakeRepository(error="workspace")
    workflow, _, _, _ = make_workflow(repository=repository)
    response = post_chat(workflow, request_body())
    assert response.status_code == 503
    assert response.json() == {"detail": "Database service is temporarily unavailable"}


def test_hindsight_recall_failure_stops_before_groq():
    timeline = []

    class Memory:
        async def recall_memories(self, *args, **kwargs):
            timeline.append("recall")
            raise MemoryRetrievalError()

        async def retain_memory(self, *args, **kwargs):
            timeline.append("retain")

    class Groq:
        def __init__(self):
            self.chat = SimpleNamespace(completions=self)

        async def create(self, **kwargs):
            timeline.append("groq")
            return None

    real_agent = SupportAgent(
        settings=Settings(groq_model="openai/gpt-oss-120b", _env_file=None),
        memory_service=Memory(),
        groq_client=Groq(),
    )
    repository = FakeRepository(timeline=timeline)
    workflow, _, _, _ = make_workflow(repository=repository, memory=Memory(), agent=real_agent)
    response = post_chat(workflow, request_body())
    assert response.status_code == 503
    assert "message:customer" in timeline
    assert "recall" in timeline
    assert "groq" not in timeline


def test_groq_failure_is_controlled_after_customer_message_is_saved():
    timeline = []

    class Memory:
        async def recall_memories(self, *args, **kwargs):
            timeline.append("recall")
            return {"results": []}

        async def retain_memory(self, *args, **kwargs):
            timeline.append("retain")

    class Groq:
        def __init__(self):
            self.chat = SimpleNamespace(completions=self)

        async def create(self, **kwargs):
            raise RuntimeError("provider detail must not leak")

    real_agent = SupportAgent(
        settings=Settings(groq_model="openai/gpt-oss-120b", _env_file=None),
        memory_service=Memory(),
        groq_client=Groq(),
    )
    repository = FakeRepository(timeline=timeline)
    workflow, _, _, _ = make_workflow(repository=repository, memory=Memory(), agent=real_agent)
    response = post_chat(workflow, request_body())
    assert response.status_code == 503
    assert "provider detail" not in response.text
    assert "message:customer" in timeline
    assert "message:assistant" not in timeline
    assert "retain" not in timeline
    assert any(call[:2] == ("activity", "workflow_stage_failed") for call in repository.calls)


def test_unknown_customer_is_404():
    repository = FakeRepository(error="customer")
    workflow, _, _, _ = make_workflow(repository=repository)
    response = post_chat(workflow, request_body())
    assert response.status_code == 404
    assert response.json() == {"detail": "Customer not found"}


def test_unknown_workspace_is_404():
    repository = FakeRepository(error="workspace_not_found")
    workflow, _, _, _ = make_workflow(repository=repository)
    response = post_chat(workflow, request_body())
    assert response.status_code == 404
    assert response.json() == {"detail": "Workspace not found"}
