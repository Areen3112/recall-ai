from datetime import datetime, timedelta, timezone
from uuid import uuid4

import jwt
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.core.security import verify_identity_token, verify_visitor_token
from app.main import create_app
from app import main as app_main
from app.memory import hindsight_client
from app.memory.memory_service import (
    BankCreationError,
    MemoryRetrievalError,
    MemoryRetentionError,
    MemoryService,
    ReflectionError,
)

BANK_SECRET = "test-hindsight-bank-secret-with-more-than-32-bytes"
IDENTITY_SECRET = "test-identity-secret-with-more-than-32-bytes"
WORKSPACE = "workspace-a"
CUSTOMER_ID = str(uuid4())


def identity_settings():
    return Settings(
        identity_token_secret=IDENTITY_SECRET,
        identity_token_issuer="recall-test-issuer",
        identity_token_audience="recall-test-audience",
        _env_file=None,
    )


def test_groq_context_budget_has_conservative_default_and_validates_configuration(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GROQ_CONTEXT_BUDGET_BYTES", raising=False)
    assert Settings(_env_file=None).groq_context_budget_bytes == 8_192
    monkeypatch.setenv("GROQ_CONTEXT_BUDGET_BYTES", "32768")
    assert Settings(_env_file=None).groq_context_budget_bytes == 32_768
    with pytest.raises(ValueError):
        Settings(groq_context_budget_bytes=1024, _env_file=None)
    for invalid_budget in (0, -1, 2_000_001):
        with pytest.raises(ValueError):
            Settings(groq_context_budget_bytes=invalid_budget, _env_file=None)
VISITOR_ID = str(uuid4())


def test_health_endpoint() -> None:
    with TestClient(create_app()) as client:
        response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_bank_ids_are_deterministic_tenant_and_subject_scoped() -> None:
    service = MemoryService(client=None, bank_id_secret=BANK_SECRET)  # type: ignore[arg-type]
    bank_id = service.bank_id(WORKSPACE, CUSTOMER_ID, subject_type="customer")
    assert bank_id == service.bank_id(WORKSPACE, CUSTOMER_ID, subject_type="customer")
    assert bank_id != service.bank_id("workspace-b", CUSTOMER_ID, subject_type="customer")
    assert bank_id != service.bank_id(WORKSPACE, CUSTOMER_ID, subject_type="visitor")
    assert CUSTOMER_ID not in bank_id


@pytest.mark.parametrize("subject_id", ["person@example.test", "customer-name", "not-a-uuid"])
def test_bank_ids_reject_non_opaque_customer_identifiers(subject_id: str) -> None:
    service = MemoryService(client=None, bank_id_secret=BANK_SECRET)  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        service.bank_id(WORKSPACE, subject_id, subject_type="customer")


def test_production_requires_distinct_long_secrets(monkeypatch: pytest.MonkeyPatch) -> None:
    for variable in ("HINDSIGHT_BANK_ID_SECRET", "IDENTITY_TOKEN_SECRET", "APP_ENV"):
        monkeypatch.delenv(variable, raising=False)
    with pytest.raises(ValueError):
        Settings(app_env="production", _env_file=None)
    shared_secret = "same-secret-value-that-is-at-least-32-bytes"
    with pytest.raises(ValueError):
        Settings(
            app_env="production",
            hindsight_bank_id_secret=shared_secret,
            identity_token_secret=shared_secret,
            _env_file=None,
        )
    settings = Settings(
        app_env="production",
        hindsight_bank_id_secret=BANK_SECRET,
        identity_token_secret=IDENTITY_SECRET,
        _env_file=None,
    )
    assert settings.app_env == "production"
    with pytest.raises(ValueError):
        Settings(
            hindsight_bank_id_secret=BANK_SECRET,
            identity_token_secret=BANK_SECRET,
            _env_file=None,
        )


def test_hindsight_client_uses_explicit_timeout_and_single_attempt(monkeypatch: pytest.MonkeyPatch) -> None:
    observed: dict = {}

    class FakeClient:
        def __init__(self, **kwargs):
            observed.update(kwargs)

    monkeypatch.setattr(hindsight_client, "Hindsight", FakeClient)
    settings = Settings(hindsight_api_key="test-key", _env_file=None)
    assert hindsight_client.create_hindsight_client(settings) is not None
    assert observed["timeout"] == 20.0
    assert observed["max_attempts"] == 1


def test_hindsight_client_closes_on_application_shutdown(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeClient:
        closed = False

        async def aclose(self):
            self.closed = True

    fake = FakeClient()
    monkeypatch.setattr(app_main, "create_hindsight_client", lambda settings: fake)
    async def no_supabase(settings):
        return None

    monkeypatch.setattr(app_main, "create_supabase_client", no_supabase)
    with TestClient(create_app()):
        assert not fake.closed
    assert fake.closed


class FakeHindsight:
    def __init__(self, fail_on: str | None = None) -> None:
        self.fail_on = fail_on
        self.calls: list[tuple[str, dict]] = []

    async def _call(self, method: str, **kwargs):
        self.calls.append((method, kwargs))
        if self.fail_on == method:
            raise RuntimeError("provider detail must not escape")
        return {"ok": True}

    async def acreate_bank(self, **kwargs):
        return await self._call("acreate_bank", **kwargs)

    async def aretain(self, **kwargs):
        return await self._call("aretain", **kwargs)

    async def arecall(self, **kwargs):
        return await self._call("arecall", **kwargs)

    async def areflect(self, **kwargs):
        return await self._call("areflect", **kwargs)


def make_service(fail_on: str | None = None) -> tuple[MemoryService, FakeHindsight]:
    client = FakeHindsight(fail_on)
    return MemoryService(client, bank_id_secret=BANK_SECRET), client  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_memory_operations_use_workspace_scoped_bank() -> None:
    service, client = make_service()
    await service.retain_memory(WORKSPACE, CUSTOMER_ID, "Issue unresolved", subject_type="customer")
    await service.recall_memories(WORKSPACE, CUSTOMER_ID, "What failed?", subject_type="customer")
    await service.reflect_memory(WORKSPACE, CUSTOMER_ID, "Summarize", subject_type="customer")
    bank_ids = [kwargs["bank_id"] for _, kwargs in client.calls]
    assert bank_ids and len(set(bank_ids)) == 1
    assert bank_ids[0] == service.bank_id(WORKSPACE, CUSTOMER_ID, subject_type="customer")
    recall = next(kwargs for method, kwargs in client.calls if method == "arecall")
    assert recall["include_source_facts"] is True


@pytest.mark.asyncio
async def test_memory_retention_forwards_sdk_document_id_without_replace_mode():
    service, client = make_service()
    await service.retain_memory(
        WORKSPACE, CUSTOMER_ID, "synthetic fixture", subject_type="customer",
        document_id="stable-fixture-v1", update_mode="append",
    )
    retain = next(kwargs for method, kwargs in client.calls if method == "aretain")
    assert retain["document_id"] == "stable-fixture-v1"
    assert retain["update_mode"] == "append"


@pytest.mark.asyncio
async def test_memory_recall_can_filter_for_structured_provenance_using_sdk_tags():
    service, client = make_service()
    await service.recall_memories(
        WORKSPACE,
        CUSTOMER_ID,
        "Which explicit troubleshooting step failed?",
        subject_type="customer",
        tags=["provenance:failed_attempt"],
        tags_match="all_strict",
    )
    recall = next(kwargs for method, kwargs in client.calls if method == "arecall")
    assert recall["tags"] == ["provenance:failed_attempt"]
    assert recall["tags_match"] == "all_strict"


@pytest.mark.asyncio
async def test_bank_creation_failure_is_sanitized() -> None:
    service, _ = make_service("acreate_bank")
    with pytest.raises(BankCreationError) as error:
        await service.ensure_bank(WORKSPACE, CUSTOMER_ID, subject_type="customer")
    assert "provider detail" not in str(error.value)


@pytest.mark.asyncio
async def test_retention_failure_is_logged_and_sanitized(caplog: pytest.LogCaptureFixture) -> None:
    service, _ = make_service("aretain")
    with pytest.raises(MemoryRetentionError) as error:
        await service.retain_memory(WORKSPACE, CUSTOMER_ID, "private content", subject_type="customer")
    assert "provider detail" not in str(error.value)
    assert "private content" not in caplog.text
    assert "Hindsight memory retention failed" in caplog.text


@pytest.mark.asyncio
async def test_retention_response_with_success_false_is_not_reported_as_stored():
    class FailedRetention(FakeHindsight):
        async def aretain(self, **kwargs):
            await self._call("aretain", **kwargs)
            return {"success": False}

    client = FailedRetention()
    service = MemoryService(client, bank_id_secret=BANK_SECRET)  # type: ignore[arg-type]
    with pytest.raises(MemoryRetentionError):
        await service.retain_memory(WORKSPACE, CUSTOMER_ID, "not retained", subject_type="customer")


@pytest.mark.asyncio
async def test_recall_failure_raises_instead_of_returning_empty_history() -> None:
    service, _ = make_service("arecall")
    with pytest.raises(MemoryRetrievalError) as error:
        await service.recall_memories(WORKSPACE, CUSTOMER_ID, "history", subject_type="customer")
    assert error.value.status_code == 503
    assert "provider detail" not in str(error.value)


@pytest.mark.asyncio
async def test_reflection_failure_is_sanitized() -> None:
    service, _ = make_service("areflect")
    with pytest.raises(ReflectionError) as error:
        await service.reflect_memory(WORKSPACE, CUSTOMER_ID, "history", subject_type="customer")
    assert "provider detail" not in str(error.value)


def make_token(claims: dict, secret: str = IDENTITY_SECRET) -> str:
    payload = {
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(minutes=5),
        "iss": "recall-test-issuer",
        "aud": "recall-test-audience",
        **claims,
    }
    return jwt.encode(payload, secret, algorithm="HS256")


def test_customer_identity_verifies_signature_expiry_workspace_and_customer() -> None:
    settings = identity_settings()
    token = make_token({"identity_type": "customer", "workspace_id": WORKSPACE, "customer_id": CUSTOMER_ID})
    identity = verify_identity_token(
        token, workspace_id=WORKSPACE, expected_customer_id=CUSTOMER_ID, settings=settings
    )
    assert identity.identity_type == "customer"
    assert identity.subject_id == CUSTOMER_ID


@pytest.mark.parametrize(
    ("claims", "workspace", "expected_customer"),
    [
        ({"identity_type": "customer", "workspace_id": "workspace-b", "customer_id": CUSTOMER_ID}, WORKSPACE, CUSTOMER_ID),
        ({"identity_type": "customer", "workspace_id": WORKSPACE, "customer_id": str(uuid4())}, WORKSPACE, CUSTOMER_ID),
        ({"identity_type": "customer", "workspace_id": WORKSPACE, "customer_id": CUSTOMER_ID}, WORKSPACE, None),
        ({"identity_type": "visitor", "workspace_id": WORKSPACE, "visitor_id": VISITOR_ID}, WORKSPACE, VISITOR_ID),
    ],
)
def test_customer_identity_rejects_mismatched_or_visitor_claims(
    claims: dict, workspace: str, expected_customer: str | None
) -> None:
    settings = identity_settings()
    with pytest.raises(Exception) as error:
        verify_identity_token(
            make_token(claims),
            workspace_id=workspace,
            expected_customer_id=expected_customer,
            settings=settings,
        )
    assert getattr(error.value, "status_code", None) == 401


@pytest.mark.parametrize("claim", ["iss", "aud"])
def test_customer_identity_rejects_wrong_issuer_or_audience(claim: str) -> None:
    settings = identity_settings()
    claims = {"identity_type": "customer", "workspace_id": WORKSPACE, "customer_id": CUSTOMER_ID}
    claims[claim] = "untrusted-value"
    with pytest.raises(Exception):
        verify_identity_token(
            make_token(claims), workspace_id=WORKSPACE, expected_customer_id=CUSTOMER_ID, settings=settings
        )


def test_customer_identity_rejects_expired_and_wrongly_signed_tokens() -> None:
    settings = identity_settings()
    claims = {"exp": datetime.now(timezone.utc) - timedelta(seconds=1),
              "identity_type": "customer", "workspace_id": WORKSPACE, "customer_id": CUSTOMER_ID}
    expired = jwt.encode(claims, IDENTITY_SECRET, algorithm="HS256")
    wrong_signature = make_token(
        {"identity_type": "customer", "workspace_id": WORKSPACE, "customer_id": CUSTOMER_ID},
        secret="wrong-signing-secret-that-is-long-enough",
    )
    for token in (expired, wrong_signature):
        with pytest.raises(Exception):
            verify_identity_token(token, workspace_id=WORKSPACE, expected_customer_id=CUSTOMER_ID, settings=settings)


def test_customer_identity_rejects_missing_iat_and_excessive_token_lifetime() -> None:
    settings = identity_settings()
    missing_iat = jwt.encode(
        {"exp": datetime.now(timezone.utc) + timedelta(minutes=5), "workspace_id": WORKSPACE,
         "identity_type": "customer", "customer_id": CUSTOMER_ID},
        IDENTITY_SECRET, algorithm="HS256",
    )
    too_long = make_token({
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(hours=2),
        "workspace_id": WORKSPACE,
        "identity_type": "customer",
        "customer_id": CUSTOMER_ID,
    })
    for token in (missing_iat, too_long):
        with pytest.raises(Exception):
            verify_identity_token(token, workspace_id=WORKSPACE, expected_customer_id=CUSTOMER_ID, settings=settings)


def test_visitor_identity_is_separate_and_cannot_authenticate_customer() -> None:
    settings = identity_settings()
    token = make_token({"identity_type": "visitor", "workspace_id": WORKSPACE, "visitor_id": VISITOR_ID})
    visitor = verify_visitor_token(
        token, workspace_id=WORKSPACE, expected_visitor_id=VISITOR_ID, settings=settings
    )
    assert visitor.identity_type == "visitor"
    assert visitor.subject_id == VISITOR_ID
    with pytest.raises(Exception):
        verify_identity_token(token, workspace_id=WORKSPACE, expected_customer_id=VISITOR_ID, settings=settings)


def test_visitor_token_rejects_customer_claim_and_workspace_mismatch() -> None:
    settings = identity_settings()
    mixed_token = make_token({
        "identity_type": "visitor", "workspace_id": WORKSPACE,
        "visitor_id": VISITOR_ID, "customer_id": CUSTOMER_ID,
    })
    valid_token_wrong_workspace = make_token(
        {"identity_type": "visitor", "workspace_id": "workspace-b", "visitor_id": VISITOR_ID}
    )
    for token in (mixed_token, valid_token_wrong_workspace):
        with pytest.raises(Exception):
            verify_visitor_token(token, workspace_id=WORKSPACE, expected_visitor_id=VISITOR_ID, settings=settings)


def test_memory_errors_are_exposed_as_sanitized_http_503() -> None:
    app = create_app()

    async def fail():
        raise MemoryRetrievalError()

    app.add_api_route("/test-memory-error", fail)
    with TestClient(app) as client:
        response = client.get("/test-memory-error")
    assert response.status_code == 503
    assert response.json() == {"detail": "Customer memory service is temporarily unavailable"}
