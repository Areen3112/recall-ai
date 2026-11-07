from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.core.performance import log_async_stage
from app.core.security import VerifiedIdentity
from app.database.chat_repository import (
    ChatRepository,
    ChatRepositoryError,
    CustomerNotFoundError,
    IdempotencyConflictError,
    InvalidSessionError,
)


class FakeQuery:
    def __init__(self, client, table: str, operation: str = "select", payload=None) -> None:
        self.client = client
        self.table_name = table
        self.operation = operation
        self.payload = payload
        self.filters = []
        self.limit_value = None

    def select(self, columns):
        self.columns = columns
        return self

    def eq(self, field, value):
        self.filters.append((field, value))
        return self

    def limit(self, value):
        self.limit_value = value
        return self

    def in_(self, field, values):
        self.filters.append((field, values))
        return self

    def contains(self, field, value):
        self.filters.append((field, value))
        return self

    def lt(self, field, value):
        self.filters.append((f"__lt__{field}", value))
        return self

    def order(self, field, *, desc=False):
        self.ordering = (field, desc)
        return self

    def insert(self, payload):
        self.operation = "insert"
        self.payload = payload
        return self

    def update(self, payload):
        self.operation = "update"
        self.payload = payload
        return self

    async def execute(self):
        self.client.operations.append((self.table_name, self.operation, list(self.filters), self.payload))
        rows = self.client.tables.setdefault(self.table_name, [])
        if self.operation == "select":
            matches = [
                row.copy()
                for row in rows
                if all(
                    (row.get(k.removeprefix("__lt__")) < v if k.startswith("__lt__")
                     else all(row.get(k, {}).get(key) == val for key, val in v.items()) if k == "metadata" and isinstance(v, dict)
                     else row.get(k) in v if isinstance(v, list) else row.get(k) == v)
                    for k, v in self.filters
                )
            ]
            if hasattr(self, "ordering"):
                field, desc = self.ordering
                matches.sort(key=lambda row: row.get(field) or "", reverse=desc)
            if self.limit_value is not None:
                matches = matches[: self.limit_value]
            return SimpleNamespace(data=matches)
        if self.operation == "insert":
            row = {"id": str(uuid4()), **self.payload}
            row.setdefault("status", "open")
            row.setdefault("sentiment", "unknown")
            row.setdefault("metadata", {})
            row.setdefault("created_at", datetime.now(timezone.utc).isoformat())
            rows.append(row)
            return SimpleNamespace(data=[row.copy()] if hasattr(self, "columns") else None)
        if self.operation == "update":
            matches = []
            for row in rows:
                if all(row.get(k) == v for k, v in self.filters):
                    row.update(self.payload)
                    matches.append(row.copy())
            return SimpleNamespace(data=matches if hasattr(self, "columns") else None)
        raise AssertionError(self.operation)


class FakeSupabase:
    def __init__(self, tables=None) -> None:
        self.tables = tables or {}
        self.operations = []

    def table(self, table_name):
        return FakeQuery(self, table_name)


@pytest.fixture
def sample_ids():
    return {
        "workspace_a": str(uuid4()),
        "workspace_b": str(uuid4()),
        "public_a": str(uuid4()),
        "customer_a": str(uuid4()),
        "customer_b": str(uuid4()),
        "conversation_a": str(uuid4()),
    }


@pytest.mark.asyncio
async def test_customer_lookup_always_filters_workspace_and_internal_id(sample_ids):
    client = FakeSupabase({"customers": [
        {"id": sample_ids["customer_b"], "workspace_id": sample_ids["workspace_b"], "total_conversations": 0,
         "identity_verified": True},
    ]})
    repository = ChatRepository(client)  # type: ignore[arg-type]
    with pytest.raises(CustomerNotFoundError):
        await repository.resolve_customer(sample_ids["workspace_a"], sample_ids["customer_b"])
    table, operation, filters, _ = client.operations[0]
    assert (table, operation) == ("customers", "select")
    assert ("workspace_id", sample_ids["workspace_a"]) in filters
    assert ("id", sample_ids["customer_b"]) in filters


@pytest.mark.asyncio
async def test_session_lookup_is_workspace_scoped_and_identity_bound(sample_ids):
    client = FakeSupabase({"conversations": [
        {
            "id": sample_ids["conversation_a"], "workspace_id": sample_ids["workspace_b"],
            "customer_id": sample_ids["customer_b"], "visitor_id": None,
            "session_id": "same-session", "status": "open", "sentiment": "unknown",
        }
    ]})
    repository = ChatRepository(client)  # type: ignore[arg-type]
    identity = VerifiedIdentity(
        workspace_id=sample_ids["workspace_a"], identity_type="customer", subject_id=sample_ids["customer_a"]
    )
    _, created = await repository.get_or_create_conversation(
        workspace_id=sample_ids["workspace_a"], identity=identity, session_id="same-session"
    )
    assert created
    lookup = client.operations[0]
    assert lookup[0:2] == ("conversations", "select")
    assert ("workspace_id", sample_ids["workspace_a"]) in lookup[2]
    inserts = [op for op in client.operations if op[1] == "insert"]
    assert inserts[0][3]["workspace_id"] == sample_ids["workspace_a"]
    assert inserts[0][3]["customer_id"] == sample_ids["customer_a"]


@pytest.mark.asyncio
async def test_existing_session_cannot_be_reused_by_another_customer(sample_ids):
    client = FakeSupabase({"conversations": [
        {
            "id": sample_ids["conversation_a"], "workspace_id": sample_ids["workspace_a"],
            "customer_id": sample_ids["customer_a"], "visitor_id": None,
            "session_id": "same-session", "status": "open", "sentiment": "unknown",
        }
    ]})
    repository = ChatRepository(client)  # type: ignore[arg-type]
    other_identity = VerifiedIdentity(
        workspace_id=sample_ids["workspace_a"], identity_type="customer", subject_id=sample_ids["customer_b"]
    )
    with pytest.raises(InvalidSessionError):
        await repository.get_or_create_conversation(
            workspace_id=sample_ids["workspace_a"], identity=other_identity, session_id="same-session"
        )


@pytest.mark.asyncio
async def test_message_and_update_operations_carry_workspace_scope(sample_ids):
    client = FakeSupabase({"conversations": [{
        "id": sample_ids["conversation_a"], "workspace_id": sample_ids["workspace_a"],
        "customer_id": sample_ids["customer_a"], "visitor_id": None,
    }]})
    repository = ChatRepository(client)  # type: ignore[arg-type]
    identity = VerifiedIdentity(
        workspace_id=sample_ids["workspace_a"], identity_type="customer", subject_id=sample_ids["customer_a"]
    )
    conversation = client.tables["conversations"][0]
    await repository.insert_message(
        workspace_id=sample_ids["workspace_a"], conversation=conversation, identity=identity,
        role="customer", content="Hello",
    )
    await repository.update_conversation(
        workspace_id=sample_ids["workspace_a"], conversation_id=sample_ids["conversation_a"],
        sentiment="neutral", last_message_at=datetime.now(timezone.utc),
    )
    for table, operation, filters, payload in client.operations:
        if table == "messages":
            assert operation == "insert"
            assert payload["workspace_id"] == sample_ids["workspace_a"]
            assert payload["conversation_id"] == sample_ids["conversation_a"]
        if table == "conversations" and operation == "update":
            assert ("workspace_id", sample_ids["workspace_a"]) in filters


@pytest.mark.asyncio
async def test_idempotency_lookup_scopes_workspace_conversation_role_and_key(sample_ids):
    key = "request-key-0000001"
    client = FakeSupabase({"messages": [{
        "id": str(uuid4()),
        "workspace_id": sample_ids["workspace_a"],
        "conversation_id": sample_ids["conversation_a"],
        "role": "customer",
        "content": "Help",
        "metadata": {"idempotency_key": key},
    }]})
    repository = ChatRepository(client)  # type: ignore[arg-type]
    row = await repository.find_idempotent_message(
        workspace_id=sample_ids["workspace_a"],
        conversation_id=sample_ids["conversation_a"],
        role="customer",
        idempotency_key=key,
    )
    assert row is not None and row["content"] == "Help"
    _, operation, filters, _ = client.operations[0]
    assert operation == "select"
    assert ("workspace_id", sample_ids["workspace_a"]) in filters
    assert ("conversation_id", sample_ids["conversation_a"]) in filters
    assert ("role", "customer") in filters
    assert ("metadata", {"idempotency_key": key}) in filters


@pytest.mark.asyncio
async def test_prior_assistant_recommendation_lookup_is_scoped_before_customer_turn(sample_ids):
    before = "2026-01-02T03:04:05+00:00"
    client = FakeSupabase({"messages": [
        {"id": "assistant-prior", "workspace_id": sample_ids["workspace_a"],
         "conversation_id": sample_ids["conversation_a"], "role": "assistant",
         "content": "Try forgetting and pairing again.", "created_at": "2026-01-02T03:00:00+00:00"},
        {"id": "assistant-future", "workspace_id": sample_ids["workspace_a"],
         "conversation_id": sample_ids["conversation_a"], "role": "assistant",
         "content": "Future response", "created_at": "2026-01-02T03:10:00+00:00"},
    ]})
    repository = ChatRepository(client)  # type: ignore[arg-type]
    row = await repository.find_prior_assistant_message(
        workspace_id=sample_ids["workspace_a"], conversation_id=sample_ids["conversation_a"],
        before_created_at=before,
    )
    assert row and row["id"] == "assistant-prior"
    _, operation, filters, _ = client.operations[0]
    assert operation == "select"
    assert ("workspace_id", sample_ids["workspace_a"]) in filters
    assert ("conversation_id", sample_ids["conversation_a"]) in filters
    assert ("role", "assistant") in filters
    assert ("__lt__created_at", before) in filters


@pytest.mark.asyncio
async def test_concurrent_idempotency_collision_with_different_content_is_409(sample_ids):
    key = "request-key-0000001"

    class ConflictQuery(FakeQuery):
        async def execute(self):
            if self.table_name == "messages" and self.operation == "insert":
                raise RuntimeError("unique index conflict")
            return await super().execute()

    class ConflictClient(FakeSupabase):
        def table(self, table_name):
            return ConflictQuery(self, table_name)

    client = ConflictClient({"messages": [{
        "id": str(uuid4()),
        "workspace_id": sample_ids["workspace_a"],
        "conversation_id": sample_ids["conversation_a"],
        "role": "customer",
        "content": "original message",
        "metadata": {"idempotency_key": key},
    }]})
    repository = ChatRepository(client)  # type: ignore[arg-type]
    identity = VerifiedIdentity(
        workspace_id=sample_ids["workspace_a"],
        identity_type="customer",
        subject_id=sample_ids["customer_a"],
    )
    conversation = {
        "id": sample_ids["conversation_a"],
        "workspace_id": sample_ids["workspace_a"],
        "customer_id": sample_ids["customer_a"],
        "visitor_id": None,
    }
    with pytest.raises(IdempotencyConflictError):
        await repository.insert_message(
            workspace_id=sample_ids["workspace_a"],
            conversation=conversation,
            identity=identity,
            role="customer",
            content="different message",
            metadata={"idempotency_key": key},
        )


@pytest.mark.asyncio
async def test_message_insert_failure_logs_safe_database_diagnostics(caplog, sample_ids):
    class FakeDatabaseError(Exception):
        status_code = 400
        code = "23514"

    class FailingQuery(FakeQuery):
        async def execute(self):
            if self.table_name == "messages" and self.operation == "insert":
                raise FakeDatabaseError("PII and provider response must not be logged")
            return await super().execute()

    class FailingClient(FakeSupabase):
        def table(self, table_name):
            return FailingQuery(self, table_name)

    identity = VerifiedIdentity(
        workspace_id=sample_ids["workspace_a"],
        identity_type="customer",
        subject_id=sample_ids["customer_a"],
    )
    conversation = {
        "id": sample_ids["conversation_a"],
        "workspace_id": sample_ids["workspace_a"],
        "customer_id": sample_ids["customer_a"],
        "visitor_id": None,
    }
    repository = ChatRepository(FailingClient())  # type: ignore[arg-type]
    caplog.set_level("WARNING", logger="app.database.chat_repository")
    with pytest.raises(ChatRepositoryError):
        async with log_async_stage("assistant_message_persistence", "safe-correlation-1234"):
            await repository.insert_message(
                workspace_id=sample_ids["workspace_a"],
                conversation=conversation,
                identity=identity,
                role="assistant",
                content="Generated response must not appear in diagnostics",
            )
    message = next(record.getMessage() for record in caplog.records if "database_operation_failed" in record.getMessage())
    assert "operation=messages.insert" in message
    assert "exception_class=FakeDatabaseError" in message
    assert "status=400" in message
    assert "database_code=23514" in message
    assert "correlation_id=safe-correlation-1234" in message
    assert "PII" not in caplog.text
    assert "Generated response" not in caplog.text
@pytest.mark.asyncio
async def test_visitor_conversation_never_gets_customer_id(sample_ids):
    client = FakeSupabase()
    repository = ChatRepository(client)  # type: ignore[arg-type]
    visitor_id = str(uuid4())
    identity = VerifiedIdentity(workspace_id=sample_ids["workspace_a"], identity_type="visitor", subject_id=visitor_id)
    conversation, created = await repository.get_or_create_conversation(
        workspace_id=sample_ids["workspace_a"], identity=identity, session_id="visitor-session"
    )
    assert created
    assert conversation["customer_id"] is None
    assert conversation["visitor_id"] == visitor_id


@pytest.mark.asyncio
async def test_escalation_ticket_lookup_and_insert_are_workspace_scoped(sample_ids):
    client = FakeSupabase()
    repository = ChatRepository(client)  # type: ignore[arg-type]
    identity = VerifiedIdentity(
        workspace_id=sample_ids["workspace_a"], identity_type="customer", subject_id=sample_ids["customer_a"]
    )
    conversation = {
        "id": sample_ids["conversation_a"], "workspace_id": sample_ids["workspace_a"],
        "customer_id": sample_ids["customer_a"], "visitor_id": None,
    }
    created = await repository.create_escalation_ticket(
        workspace_id=sample_ids["workspace_a"], conversation=conversation, identity=identity
    )
    assert created
    lookup = client.operations[0]
    assert lookup[0:2] == ("support_tickets", "select")
    assert ("workspace_id", sample_ids["workspace_a"]) in lookup[2]
    ticket_insert = client.operations[1][3]
    assert ticket_insert["workspace_id"] == sample_ids["workspace_a"]
    assert ticket_insert["conversation_id"] == sample_ids["conversation_a"]


@pytest.mark.asyncio
async def test_supabase_client_missing_service_role_key_never_falls_back(monkeypatch):
    from app.database import supabase as supabase_module
    from app.core.config import Settings

    for variable in ("SUPABASE_URL", "SUPABASE_KEY", "SUPABASE_SERVICE_ROLE_KEY"):
        monkeypatch.delenv(variable, raising=False)
    monkeypatch.setenv("SUPABASE_KEY", "publishable-test-value")
    settings_without_service_key = Settings(supabase_url="https://example.supabase.co", _env_file=None)
    assert settings_without_service_key.supabase_service_role_key is None
    assert await supabase_module.create_supabase_client(settings_without_service_key) is None


@pytest.mark.asyncio
async def test_supabase_client_initializes_with_explicit_service_role_key(monkeypatch):
    from app.database import supabase as supabase_module
    from app.core.config import Settings

    for variable in ("SUPABASE_URL", "SUPABASE_KEY", "SUPABASE_SERVICE_ROLE_KEY"):
        monkeypatch.delenv(variable, raising=False)
    monkeypatch.setenv("SUPABASE_KEY", "publishable-test-value")

    observed = {}

    class FakePostgrest:
        closed = False

        async def aclose(self):
            self.closed = True

    class FakeAuth:
        closed = False

        async def close(self):
            self.closed = True

    class FakeClient:
        def __init__(self):
            self.postgrest = FakePostgrest()
            self.auth = FakeAuth()

    fake = FakeClient()

    async def make_async_client(url, key):
        observed["url"] = url
        observed["key"] = key
        return fake

    monkeypatch.setattr(supabase_module, "create_async_client", make_async_client)
    settings = Settings(
        supabase_url="https://example.supabase.co",
        supabase_service_role_key="fake-service-role-for-test",
        _env_file=None,
    )
    assert await supabase_module.create_supabase_client(settings) is fake
    assert observed["key"] == "fake-service-role-for-test"
    await supabase_module.close_supabase_client(fake)  # type: ignore[arg-type]
    assert fake.postgrest.closed and fake.auth.closed
