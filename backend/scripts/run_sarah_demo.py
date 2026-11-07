"""Run a synthetic cross-session Sarah memory-learning scenario against local API."""

import asyncio
from dataclasses import dataclass
import fcntl
import hashlib
import json
import logging
import math
import os
from pathlib import Path
import sys
import tempfile
from uuid import UUID, uuid4

import httpx
from fastapi import HTTPException


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.core.config import Settings  # noqa: E402
from app.core.security import verify_identity_token  # noqa: E402
from app.memory.hindsight_client import create_hindsight_client  # noqa: E402
from app.memory.memory_service import MemoryService  # noqa: E402
from app.agents.troubleshooting_actions import (  # noqa: E402
    BLUETOOTH_REPAIR_ACTION,
    failed_action_response_status,
    recommended_action_ids,
)


DEMO_FILE = BACKEND_DIR / ".sarah_demo.json"
DEMO_NAMESPACE = "demo-sarah-mitchell-v1"
HTTP_TIMEOUT_ENV = "SARAH_DEMO_HTTP_TIMEOUT_SECONDS"
DEFAULT_HTTP_TIMEOUT_SECONDS = 45.0
_VERIFICATION_LOGGER = logging.getLogger("uvicorn.error.sarah_demo_verification")
_PREFLIGHT_LOGGER = logging.getLogger("uvicorn.error.sarah_demo_preflight")


class DemoIdentityTokenError(RuntimeError):
    """The stored local demo token is expired or no longer matches local settings."""


class DemoValidationError(RuntimeError):
    """A safe, phase-specific demo check failed."""

    def __init__(self, phase: str, condition: str) -> None:
        self.phase = phase
        self.condition = condition
        super().__init__(f"phase={phase} condition={condition}")


@dataclass(frozen=True)
class DemoInteraction:
    phase: str
    session_id: str
    idempotency_key: str
    message: str


def build_scenario(run_id: UUID | None = None) -> tuple[DemoInteraction, ...]:
    """Create stable scenario content with fresh run-scoped sessions and keys."""
    run_token = (run_id or uuid4()).hex
    learning_session = f"sarah-demo-v2-{run_token}-learn"
    recall_session = f"sarah-demo-v2-{run_token}-recall"
    messages = (
        (
            "suggest_step",
            learning_session,
            "My Bluetooth headphones disconnect about every 10 minutes. Restarting Bluetooth and the headphones did not help. Please suggest one different step: forgetting these headphones in Bluetooth settings and pairing them again.",
        ),
        (
            "report_failure",
            learning_session,
            "I followed your suggestion to forget these headphones in Bluetooth settings and pair them again. It did not help; they still disconnect after about 10 minutes.",
        ),
        (
            "cross_session_recall",
            recall_session,
            "My Bluetooth headphones disconnected again. Based on my previous support history, what different troubleshooting step should I try?",
        ),
    )
    return tuple(
        DemoInteraction(
            phase=phase,
            session_id=session_id,
            idempotency_key=f"sarah-demo-v2-{run_token}-{index:02d}",
            message=message,
        )
        for index, (phase, session_id, message) in enumerate(messages, start=1)
    )


def get_http_timeout_seconds(value: str | None = None) -> float:
    """Read a bounded demo-only timeout without changing provider timeouts."""
    raw_value = os.getenv(HTTP_TIMEOUT_ENV) if value is None else value
    if raw_value is None:
        return DEFAULT_HTTP_TIMEOUT_SECONDS
    try:
        timeout_seconds = float(raw_value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{HTTP_TIMEOUT_ENV} must be a number between 1 and 3600") from exc
    if not math.isfinite(timeout_seconds) or not 1 <= timeout_seconds <= 3600:
        raise ValueError(f"{HTTP_TIMEOUT_ENV} must be a number between 1 and 3600")
    return timeout_seconds


def verify_demo_identity_config(config: dict, settings: Settings | None = None) -> None:
    """Reject stale demo credentials locally before sending a chat request."""
    settings = settings or Settings(_env_file=BACKEND_DIR / ".env")
    try:
        verify_identity_token(
            config["identity_token"],
            workspace_id=config["workspace_id"],
            expected_customer_id=config["customer_id"],
            settings=settings,
        )
    except (HTTPException, KeyError, TypeError, ValueError):
        raise DemoIdentityTokenError() from None


def _recall_results(recall_result):
    if isinstance(recall_result, dict):
        results = recall_result.get("results", [])
        source_facts = recall_result.get("source_facts", {})
    else:
        results = getattr(recall_result, "results", [])
        source_facts = getattr(recall_result, "source_facts", {})
    combined = list(results) if isinstance(results, (list, tuple)) else []
    if isinstance(source_facts, dict):
        combined.extend(source_facts.values())
    return combined


def _is_failed_attempt_candidate(result) -> bool:
    if isinstance(result, dict):
        metadata, tags = result.get("metadata"), result.get("tags")
    else:
        metadata, tags = getattr(result, "metadata", None), getattr(result, "tags", None)
    metadata = metadata if isinstance(metadata, dict) else {}
    tags = tags if isinstance(tags, (list, tuple, set)) else ()
    return (
        metadata.get("provenance_kind") == "failed_attempt"
        or "provenance:failed_attempt" in tags
    )


_FAILED_ATTEMPT_PREDICATES = (
    "memory_id_present",
    "recall_text_present",
    "metadata_present",
    "failed_attempt_provenance",
    "customer_report_confirmation",
    "independently_unverified",
    "session_fingerprint_match",
    "statement_digest_match",
    "prior_recommendation_linked",
    "prior_recommendation_id_present",
    "action_ids_present",
    "expected_action_id_match",
    "failed_attempt_tag_present",
    "customer_report_tag_present",
)


def _failed_attempt_predicates(
    result, *, session_fingerprint: str, statement_sha256: str
) -> tuple[str | None, dict[str, bool]]:
    """Evaluate one recall representation without comparing extracted text to source text."""
    if isinstance(result, dict):
        memory_id, text = result.get("id"), result.get("text")
        metadata, tags = result.get("metadata"), result.get("tags")
    else:
        memory_id, text = getattr(result, "id", None), getattr(result, "text", None)
        metadata, tags = getattr(result, "metadata", None), getattr(result, "tags", None)

    metadata = metadata if isinstance(metadata, dict) else {}
    tag_set = {tag for tag in tags if isinstance(tag, str)} if isinstance(tags, (list, tuple)) else set()
    raw_action_ids = metadata.get("action_ids")
    action_ids = set(raw_action_ids.split(",")) if isinstance(raw_action_ids, str) else set()
    recommendation_id = metadata.get("prior_recommendation_message_id")
    predicates = {
        "memory_id_present": isinstance(memory_id, str) and bool(memory_id),
        "recall_text_present": isinstance(text, str),
        "metadata_present": isinstance(result.get("metadata"), dict) if isinstance(result, dict) else isinstance(getattr(result, "metadata", None), dict),
        "failed_attempt_provenance": metadata.get("provenance_kind") == "failed_attempt",
        "customer_report_confirmation": metadata.get("confirmation_source") == "customer_report",
        "independently_unverified": metadata.get("independently_verified") == "false",
        "session_fingerprint_match": metadata.get("session_fingerprint") == session_fingerprint,
        "statement_digest_match": (
            isinstance(metadata.get("customer_statement_sha256"), str)
            and metadata.get("customer_statement_sha256") == statement_sha256
        ),
        "prior_recommendation_linked": metadata.get("linked_to_prior_recommendation") == "true",
        "prior_recommendation_id_present": isinstance(recommendation_id, str) and bool(recommendation_id),
        "action_ids_present": isinstance(raw_action_ids, str) and bool(action_ids),
        "expected_action_id_match": BLUETOOTH_REPAIR_ACTION in action_ids,
        "failed_attempt_tag_present": "provenance:failed_attempt" in tag_set,
        "customer_report_tag_present": "confirmation:customer_report" in tag_set,
    }
    return memory_id if isinstance(memory_id, str) else None, predicates


def find_current_failed_attempt_ids(
    recall_result, *, session_fingerprint: str, statement_sha256: str
) -> set[str]:
    """Require exact structural provenance and the digest of this run's source statement."""
    relevant_ids: set[str] = set()
    for result in _recall_results(recall_result):
        memory_id, predicates = _failed_attempt_predicates(
            result, session_fingerprint=session_fingerprint, statement_sha256=statement_sha256
        )
        if memory_id and all(predicates.values()):
            relevant_ids.add(memory_id)
    return relevant_ids


def _log_failed_attempt_predicates(
    candidates: list, *, session_fingerprint: str, statement_sha256: str
) -> set[str]:
    """Log boolean-only diagnostics and return records passing every predicate."""
    diagnostic_id = uuid4()
    relevant_ids: set[str] = set()
    if not candidates:
        values = {name: False for name in _FAILED_ATTEMPT_PREDICATES}
        values["candidate_present"] = False
        _VERIFICATION_LOGGER.warning(
            "sarah_demo_failed_attempt_predicates diagnostic_id=%s %s",
            diagnostic_id,
            " ".join(f"{name}={str(value).lower()}" for name, value in values.items()),
        )
        return relevant_ids

    for index, result in enumerate(candidates):
        memory_id, predicates = _failed_attempt_predicates(
            result, session_fingerprint=session_fingerprint, statement_sha256=statement_sha256
        )
        predicates = {"candidate_present": True, **predicates}
        _VERIFICATION_LOGGER.info(
            "sarah_demo_failed_attempt_predicates diagnostic_id=%s candidate_index=%d %s",
            diagnostic_id,
            index,
            " ".join(f"{name}={str(value).lower()}" for name, value in predicates.items()),
        )
        if memory_id and all(predicates.values()):
            relevant_ids.add(memory_id)
    return relevant_ids


def _recommends_pairing_step(response: str) -> bool:
    """Narrow action recognition for phase-one scenario setup, not a semantic proof."""
    return BLUETOOTH_REPAIR_ACTION in recommended_action_ids(response)


def validate_phase_one_recommendation(response: str) -> None:
    """Require the exact action the next scripted customer turn reports trying."""
    if not _recommends_pairing_step(response):
        raise DemoValidationError("phase1", "required_forget_and_pair_action_not_detected")


def claim_demo_configuration(path: Path) -> dict:
    """Mark a seeded customer as consumed so a new execution requires a new seed."""
    lock_path = path.with_name(f"{path.name}.lock")
    lock_fd = os.open(lock_path, os.O_CREAT | os.O_RDWR, 0o600)
    try:
        os.fchmod(lock_fd, 0o600)
        try:
            fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise DemoValidationError("preflight", "another_demo_runner_is_starting") from None

        config = json.loads(path.read_text(encoding="utf-8"))
        if config.get("synthetic_data") is not True or config.get("demo_namespace") != DEMO_NAMESPACE:
            raise DemoValidationError("preflight", "synthetic_demo_configuration_required")
        try:
            customer_id = str(UUID(config.get("customer_id", "")))
            demo_run_id = str(UUID(config.get("demo_run_id", "")))
        except (ValueError, TypeError, AttributeError):
            raise DemoValidationError("preflight", "demo_identity_is_invalid") from None
        if customer_id != demo_run_id:
            raise DemoValidationError("preflight", "demo_run_identity_mismatch")
        if config.get("run_status") != "ready":
            raise DemoValidationError("preflight", "demo_configuration_already_used_reseed_required")

        config["customer_id"] = customer_id
        config["demo_run_id"] = demo_run_id
        config["run_status"] = "started"
        descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
        temporary_path = Path(temporary_name)
        try:
            os.fchmod(descriptor, 0o600)
            with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
                json.dump(config, stream, indent=2)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary_path, path)
            os.chmod(path, 0o600)
        except Exception:
            try:
                os.close(descriptor)
            except OSError:
                pass
            temporary_path.unlink(missing_ok=True)
            raise
        return config
    finally:
        try:
            fcntl.flock(lock_fd, fcntl.LOCK_UN)
        finally:
            os.close(lock_fd)


def _interaction_payload(config: dict, interaction: DemoInteraction) -> dict:
    return {
        "customer_id": config["customer_id"],
        "identity_token": config["identity_token"],
        "session_id": interaction.session_id,
        "message": interaction.message,
    }


async def _post_interaction(client: httpx.AsyncClient, config: dict, interaction: DemoInteraction) -> dict:
    response = await client.post(
        "/api/v1/chat",
        headers={
            "X-Workspace-ID": config["workspace_public_id"],
            "Idempotency-Key": interaction.idempotency_key,
        },
        json=_interaction_payload(config, interaction),
    )
    workflow_status = response.headers.get("X-Workflow-Status")
    memory_status = response.headers.get("X-Memory-Status")
    if response.status_code != 200:
        raise DemoValidationError(interaction.phase, "http_status_not_200")
    if workflow_status not in (None, "complete"):
        raise DemoValidationError(interaction.phase, "workflow_status_not_complete")
    if memory_status not in (None, "stored"):
        raise DemoValidationError(interaction.phase, "memory_status_not_stored")
    return response.json()


def demo_final_decision(avoidance_status: str, human_answer: str, *, relevant_memory_used: bool = True) -> bool:
    """A demo success requires explicit human confirmation of the final response."""
    return relevant_memory_used and avoidance_status in {"avoided", "uncertain"} and human_answer.strip().lower() in {
        "yes", "y", "confirmed"
    }


async def _verify_hindsight_failure(config: dict, interaction: DemoInteraction) -> set[str]:
    settings = Settings(_env_file=BACKEND_DIR / ".env")
    if (
        not settings.hindsight_api_key
        or not settings.hindsight_bank_id_secret
        or not settings.identity_token_secret
        or not settings.identity_token_issuer
        or not settings.identity_token_audience
    ):
        raise RuntimeError("Demo identity or Hindsight verification configuration is unavailable")
    identity = verify_identity_token(
        config["identity_token"],
        workspace_id=config["workspace_id"],
        expected_customer_id=config["customer_id"],
        settings=settings,
    )
    hindsight = create_hindsight_client(settings)
    if hindsight is None:
        raise RuntimeError("Hindsight verification client is unavailable")
    try:
        memory_service = MemoryService(hindsight, bank_id_secret=settings.hindsight_bank_id_secret)
        recall = await memory_service.recall_memories(
            identity.workspace_id,
            identity.subject_id,
            interaction.message,
            subject_type="customer",
            tags=["provenance:failed_attempt"],
            tags_match="all_strict",
        )
        session_fingerprint = hashlib.sha256(interaction.session_id.encode("utf-8")).hexdigest()
        statement_sha256 = hashlib.sha256(interaction.message.encode("utf-8")).hexdigest()
        candidates = _recall_results(recall)
        relevant_ids = _log_failed_attempt_predicates(
            candidates,
            session_fingerprint=session_fingerprint,
            statement_sha256=statement_sha256,
        )
        if not relevant_ids:
            reason = "no_tagged_results" if not candidates else "metadata_or_session_mismatch"
            _VERIFICATION_LOGGER.warning(
                "sarah_demo_failed_attempt_verification outcome=query_miss reason=%s diagnostic_id=%s",
                reason,
                uuid4(),
            )
            raise DemoValidationError("hindsight_verification", "current_failed_attempt_not_found")
        _VERIFICATION_LOGGER.info(
            "sarah_demo_failed_attempt_verification outcome=found diagnostic_id=%s",
            uuid4(),
        )
        return relevant_ids
    finally:
        await hindsight.aclose()


async def _verify_clean_demo_bank(config: dict) -> None:
    """Refuse to start a scripted run from a bank with an earlier failed action."""
    settings = Settings(_env_file=BACKEND_DIR / ".env")
    if (
        not settings.hindsight_api_key
        or not settings.hindsight_bank_id_secret
        or not settings.identity_token_secret
        or not settings.identity_token_issuer
        or not settings.identity_token_audience
    ):
        raise RuntimeError("Demo identity or Hindsight verification configuration is unavailable")
    identity = verify_identity_token(
        config["identity_token"],
        workspace_id=config["workspace_id"],
        expected_customer_id=config["customer_id"],
        settings=settings,
    )
    hindsight = create_hindsight_client(settings)
    if hindsight is None:
        raise RuntimeError("Hindsight verification client is unavailable")
    try:
        memory_service = MemoryService(hindsight, bank_id_secret=settings.hindsight_bank_id_secret)
        recall = await memory_service.recall_memories(
            identity.workspace_id,
            identity.subject_id,
            "Existing customer-reported failed troubleshooting attempts",
            subject_type="customer",
            tags=["provenance:failed_attempt"],
            tags_match="all_strict",
        )
        candidates = _recall_results(recall)
        contaminated = any(_is_failed_attempt_candidate(result) for result in candidates)
        if contaminated:
            _PREFLIGHT_LOGGER.warning(
                "sarah_demo_bank_preflight outcome=blocked reason=prior_failed_attempt_present"
            )
            raise DemoValidationError("preflight", "demo_bank_not_clean_reseed_required")
        _PREFLIGHT_LOGGER.info("sarah_demo_bank_preflight outcome=clean")
    finally:
        await hindsight.aclose()


async def run() -> None:
    if not DEMO_FILE.exists():
        raise DemoValidationError("preflight", "run_seed_sarah_demo_first")
    config = claim_demo_configuration(DEMO_FILE)
    if config.get("synthetic_data") is not True or config.get("demo_namespace") != DEMO_NAMESPACE:
        raise DemoValidationError("preflight", "synthetic_demo_configuration_required")
    if not all(config.get(field) for field in ("workspace_public_id", "workspace_id", "customer_id", "identity_token")):
        raise DemoValidationError("preflight", "demo_configuration_incomplete")
    try:
        for field in ("workspace_public_id", "workspace_id", "customer_id"):
            config[field] = str(UUID(config[field]))
    except (ValueError, TypeError, AttributeError):
        raise DemoValidationError("preflight", "demo_configuration_has_invalid_identifiers") from None

    verify_demo_identity_config(config)
    await _verify_clean_demo_bank(config)

    scenario = build_scenario()
    async with httpx.AsyncClient(
        base_url="http://127.0.0.1:8000", timeout=get_http_timeout_seconds()
    ) as client:
        suggested = await _post_interaction(client, config, scenario[0])
        print("Phase 1 | Sarah reports the recurring issue; the agent suggests a step")
        print(suggested["response"])
        validate_phase_one_recommendation(suggested["response"])

        failed = await _post_interaction(client, config, scenario[1])
        print("\nPhase 2 | Sarah reports that the suggested step failed")
        print(failed["response"])

        relevant_memory_ids = await _verify_hindsight_failure(config, scenario[1])
        print("\nHindsight verification | This run's customer-reported failed step was recalled")

        recalled = await _post_interaction(client, config, scenario[2])
        used_relevant_memory = relevant_memory_ids.intersection(recalled.get("memories_used") or [])
        avoidance_status = failed_action_response_status(
            recalled.get("response", ""), {BLUETOOTH_REPAIR_ACTION}
        )
        if avoidance_status == "repeat":
            raise DemoValidationError("phase3", "failed_action_recommended_again")
        print("\nPhase 3 | New session response after Hindsight recall")
        print(recalled["response"])
        print("\nFinal verification")
        print("Memory retrieved: yes")
        print("Correct failure record verified: yes")
        print(f"Agent identified the recalled failure as used: {'yes' if used_relevant_memory else 'no'}")
        print(f"Agent response passed avoidance check: {'yes' if avoidance_status == 'avoided' else avoidance_status}")
        print("Human review required: yes (the phrase validator is not a complete semantic validator)")
        answer = input("After reviewing the response, did it avoid the failed pairing step? [yes/no]: ")
        if not demo_final_decision(
            avoidance_status, answer, relevant_memory_used=bool(used_relevant_memory)
        ):
            if not used_relevant_memory:
                condition = "verified_failure_memory_not_used"
            elif avoidance_status == "uncertain":
                condition = "human_review_did_not_confirm_uncertain_avoidance"
            else:
                condition = "human_review_not_confirmed"
            raise DemoValidationError("final_review", condition)
        print("Human review: confirmed")
        print("Sarah cross-session memory scenario: verified with human review.")


def main() -> None:
    try:
        asyncio.run(run())
    except DemoIdentityTokenError:
        print(
            "Sarah demo identity token is expired or invalid for current local settings; "
            "rerun scripts/seed_sarah_demo.py for the same configured workspace.",
            file=sys.stderr,
        )
        raise SystemExit(1) from None
    except DemoValidationError as exc:
        print(f"Sarah demo validation failed: phase={exc.phase} condition={exc.condition}.")
        raise SystemExit(1) from None
    except Exception as exc:
        print(f"Sarah demo request failed ({type(exc).__name__}).")
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
