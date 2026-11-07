import json
import logging
import re
from typing import Any
from uuid import uuid4

from groq import AsyncGroq
from pydantic import ValidationError

from app.core.config import Settings
from app.core.performance import log_async_stage
from app.core.security import VerifiedIdentity
from app.agents.prompts import (
    FAILED_ACTION_CONSTRAINT_PROMPT,
    FAILED_ACTION_CORRECTION_PROMPT,
    SYSTEM_PROMPT,
    build_user_context,
)
from app.agents.troubleshooting_actions import (
    BLUETOOTH_REPAIR_ACTION,
    failed_action_response_status,
)
from app.memory.memory_service import MemoryService, SubjectType
from app.schemas.agent import SUPPORT_AGENT_JSON_SCHEMA, SupportAgentOutput

logger = logging.getLogger(__name__)
_CONTEXT_SIZE_LOGGER = logging.getLogger("uvicorn.error.groq_context_size")
_ACTION_VALIDATION_LOGGER = logging.getLogger("uvicorn.error.support_action_validation")


class SupportAgentError(Exception):
    status_code = 503
    public_message = "The support agent is temporarily unavailable"


class GroqGenerationError(SupportAgentError):
    pass


class InvalidAgentOutputError(SupportAgentError):
    status_code = 502
    public_message = "The support agent returned an invalid response"


_STRICT_JSON_SCHEMA_MODELS = {
    "openai/gpt-oss-20b",
    "openai/gpt-oss-120b",
    "qwen/qwen3.8-27b",
}
_MAX_OUTPUT_ATTEMPTS = 2
_REQUEST_OVERHEAD_BYTES = 1024
_PROVENANCE_LABELS = {
    "customer_reported", "failed_attempt", "successful_attempt",
    "confirmed_resolution", "unresolved_issue", "model_suggestion",
    "business_context", "unclassified_historical_memory",
}
_MEMORY_PRIORITY = {
    "failed_attempt": 0,
    "customer_reported": 1,
    "unresolved_issue": 2,
    "successful_attempt": 3,
    "confirmed_resolution": 4,
    "business_context": 5,
    "model_suggestion": 6,
    "unclassified_historical_memory": 7,
}
_RESOLUTION_ASSERTION = re.compile(
    r"\bit\s+(?:is|was|has been|has)\s+(?:now\s+)?(?:fixed|resolved|solved|working)(?:\s+now)?\b"
    r"|\bit's\s+(?:now\s+)?(?:fixed|resolved|solved|working)(?:\s+now)?\b"
    r"|\b(?:this|(?:your|the)\s+(?:issue|problem|request)|issue|problem)\s+"
    r"(?:is|was|has been|has)\s+(?:now\s+)?(?:fixed|resolved|solved|working)(?:\s+now)?\b"
    r"|\b(?:i|we)(?:'ve| have)?\s+(?:fixed|resolved|solved)\s+(?:it|the\s+(?:issue|problem))\b"
    r"|\b(?:you're|you are)\s+all set\b"
    r"|\bglad\s+(?:it's|it is|that\s+(?:the\s+)?(?:issue|problem)\s+(?:is|was)?)\s+(?:fixed|resolved|solved)\b",
    re.IGNORECASE,
)
_CUSTOMER_CONFIRMED_RESOLUTION = re.compile(
    r"\b(?:it(?:'s| is)\s+(?:working|fixed|resolved|solved)(?:\s+now)?|"
    r"that\s+(?:fixed|solved|resolved)\s+(?:it|the\s+(?:issue|problem))|"
    r"(?:it\s+)?works\s+now|(?:issue|problem)\s+(?:is\s+)?(?:fixed|resolved|solved)\s+now|"
    r"all\s+good\s+now)\b",
    re.IGNORECASE,
)
_NEGATED_CONFIRMATION = re.compile(r"\b(?:not|still|never|isn't|isnt|didn't|doesn't|hasn't|haven't)\b", re.IGNORECASE)
_RESOLUTION_DENIAL = re.compile(
    r"\b(?:can['’]t|cannot|can not)\s+(?:confirm|say|verify|claim|state)\b|"
    r"\b(?:not|isn't|isnt|wasn't|wasnt|hasn't|hasnt)\s+(?:yet\s+)?$",
    re.IGNORECASE,
)


def _has_unconfirmed_resolution_claim(text: str) -> bool:
    for match in _RESOLUTION_ASSERTION.finditer(text):
        preceding_text = text[max(0, match.start() - 80) : match.start()]
        if _RESOLUTION_DENIAL.search(preceding_text):
            continue
        return True
    return False


class SupportAgent:
    """Retrieve verified-subject memory and generate a structured support response.

    The agent never writes memory. Its suggested facts are candidates for a separate,
    future persistence decision after verification by the chat workflow.
    """

    def __init__(
        self,
        *,
        settings: Settings,
        memory_service: MemoryService,
        groq_client: Any | None = None,
    ) -> None:
        self.settings = settings
        self.memory_service = memory_service
        self._owns_groq_client = groq_client is None
        if groq_client is None:
            if not settings.groq_api_key:
                raise ValueError("GROQ_API_KEY is required to initialize the support agent")
            groq_client = AsyncGroq(
                api_key=settings.groq_api_key.get_secret_value(),
                timeout=settings.groq_timeout_seconds,
            )
        self.groq_client = groq_client

    async def aclose(self) -> None:
        if self._owns_groq_client:
            await self.groq_client.close()

    async def respond(
        self,
        *,
        workspace_id: str,
        identity: VerifiedIdentity,
        current_message: str,
        authorized_business_context: str = "",
        correlation_id: str | None = None,
        reported_failed_action_ids: set[str] | None = None,
    ) -> SupportAgentOutput:
        if not workspace_id or identity.workspace_id != workspace_id:
            raise ValueError("Verified identity must be bound to the requested workspace")
        if not current_message.strip():
            raise ValueError("Current customer message cannot be empty")

        subject_type: SubjectType = identity.identity_type
        timing_correlation_id = correlation_id or str(uuid4())
        # Recall happens before any Groq request. Failures propagate as the existing
        # MemoryRetrievalError (mapped to a sanitized HTTP 503 by the application).
        async with log_async_stage("hindsight_memory_recall", timing_correlation_id):
            recall_result = await self.memory_service.recall_memories(
                workspace_id,
                identity.subject_id,
                current_message,
                subject_type=subject_type,
            )
        memory_context = self._memory_context(recall_result)
        if any(memory.get("safety_conflict", False) for memory in memory_context):
            safe_context = self._serialize_context(
                current_message=current_message,
                authorized_business_context=authorized_business_context,
                memories=[],
                failed_action_ids=set(),
            )
            self._log_context_measurements(
                user_context=safe_context,
                memories=memory_context,
                outcome="provenance_conflict",
                correlation_id=timing_correlation_id,
                selected_memories=[],
            )
            return self._budget_escalation(
                bool(memory_context), timing_correlation_id, outcome="provenance_conflict"
            )
        failed_action_ids = set(reported_failed_action_ids or ())
        for memory in memory_context:
            failed_action_ids.update(self._failed_action_ids_from_memory(memory))
        unknown_failed_actions = failed_action_ids - {BLUETOOTH_REPAIR_ACTION}
        failed_action_ids.update(unknown_failed_actions)
        selected_memories = self._select_memories(
            memory_context,
            current_message=current_message,
            authorized_business_context=authorized_business_context,
            failed_action_ids=failed_action_ids,
        )
        if selected_memories is None:
            mandatory_context = [
                item for item in memory_context if self._is_mandatory_failure(item)
            ]
            overflow_context = self._serialize_context(
                current_message=current_message,
                authorized_business_context=authorized_business_context,
                memories=mandatory_context,
                failed_action_ids=failed_action_ids,
            )
            self._log_context_measurements(
                user_context=overflow_context,
                memories=memory_context,
                outcome="mandatory_context_overflow" if any(self._is_mandatory_failure(item) for item in memory_context) else "context_overflow",
                correlation_id=timing_correlation_id,
                selected_memories=mandatory_context,
            )
            return self._budget_escalation(bool(memory_context), timing_correlation_id)
        user_context = self._serialize_context(
            current_message=current_message,
            authorized_business_context=authorized_business_context,
            memories=selected_memories,
            failed_action_ids=failed_action_ids,
        )
        allowed_memory_ids = {
            memory_id
            for memory in selected_memories
            for memory_id in [memory["id"], *memory.get("duplicate_ids", [])]
        }
        confirmed_resolution = self._customer_confirmed_resolution(current_message)

        for attempt in range(_MAX_OUTPUT_ATTEMPTS):
            system_prompt = self._system_prompt(
                correction=attempt > 0,
                has_failed_constraints=bool(failed_action_ids),
            )
            self._log_context_measurements(
                user_context=user_context,
                memories=memory_context,
                outcome="ready",
                correlation_id=timing_correlation_id,
                system_prompt=system_prompt,
                selected_memories=selected_memories,
            )
            try:
                async with log_async_stage("groq_generation", timing_correlation_id):
                    raw_content = await self._generate(user_context, correction=attempt > 0)
            except Exception as exc:
                status_code = getattr(exc, "status_code", None)
                safe_status = (
                    status_code
                    if isinstance(status_code, int) and not isinstance(status_code, bool) and 100 <= status_code <= 599
                    else "unavailable"
                )
                logger.warning(
                    "groq_generation_failed exception_class=%s status=%s correlation_id=%s",
                    type(exc).__name__,
                    safe_status,
                    timing_correlation_id,
                )
                raise GroqGenerationError() from None
            try:
                output = SupportAgentOutput.model_validate_json(raw_content)
            except (ValidationError, ValueError, TypeError):
                _ACTION_VALIDATION_LOGGER.info(
                    "support_action_validation outcome=retry reason=structured_output_invalid "
                    "attempt=%d correlation_id=%s",
                    attempt + 1,
                    timing_correlation_id,
                )
                continue

            if not confirmed_resolution and (
                _has_unconfirmed_resolution_claim(output.response)
                or _has_unconfirmed_resolution_claim(output.interaction_summary)
            ):
                _ACTION_VALIDATION_LOGGER.info(
                    "support_action_validation outcome=retry reason=unconfirmed_resolution_claim "
                    "attempt=%d correlation_id=%s",
                    attempt + 1,
                    timing_correlation_id,
                )
                continue

            avoidance_status = failed_action_response_status(output.response, failed_action_ids)
            if avoidance_status != "avoided":
                validation_reason = (
                    "failed_action_repeat" if avoidance_status == "repeat"
                    else "failed_action_uncertain"
                )
                if attempt == 0:
                    _ACTION_VALIDATION_LOGGER.info(
                        "support_action_validation outcome=retry reason=%s attempt=%d correlation_id=%s",
                        validation_reason,
                        attempt + 1,
                        timing_correlation_id,
                    )
                    continue
                _ACTION_VALIDATION_LOGGER.info(
                    "support_action_validation outcome=escalated reason=%s attempt=%d correlation_id=%s",
                    validation_reason,
                    attempt + 1,
                    timing_correlation_id,
                )
                # Never return a potentially repeated or ambiguous recommendation as
                # if it passed. The chat workflow can create a human escalation.
                output = SupportAgentOutput(
                    response=(
                        "I want to avoid repeating a step that you reported did not help. "
                        "I’ll have a support specialist review this history before suggesting another step."
                    ),
                    sentiment=output.sentiment,
                    memories_used=[],
                    memory_retrieved=bool(memory_context),
                    escalation_required=True,
                    escalation_reason="Troubleshooting history requires human review before another step.",
                    interaction_summary="The response was escalated because avoiding a reported failed step could not be validated.",
                    suggested_memory_facts=[],
                )
                return output

            if output.escalation_required:
                _ACTION_VALIDATION_LOGGER.info(
                    "support_action_validation outcome=escalated reason=model_requested_escalation "
                    "attempt=%d correlation_id=%s",
                    attempt + 1,
                    timing_correlation_id,
                )
            else:
                _ACTION_VALIDATION_LOGGER.info(
                    "support_action_validation outcome=accepted reason=%s "
                    "attempt=%d correlation_id=%s",
                    "failed_action_avoided" if failed_action_ids else "no_failed_action_constraint",
                    attempt + 1,
                    timing_correlation_id,
                )

            # Never trust model-generated memory references. Restrict the list to IDs
            # returned by this workspace/subject recall operation.
            output.memories_used = [item for item in output.memories_used if item in allowed_memory_ids]
            output.memory_retrieved = bool(memory_context)
            if not confirmed_resolution:
                output.suggested_memory_facts = [
                    fact for fact in output.suggested_memory_facts if not _has_unconfirmed_resolution_claim(fact)
                ]
            return output

        raise InvalidAgentOutputError() from None

    async def _generate(self, user_context: str, *, correction: bool) -> str:
        system_prompt = self._system_prompt(
            correction=correction,
            has_failed_constraints='"failed_action_constraints"' in user_context,
        )
        kwargs: dict[str, Any] = {
            "model": self.settings.groq_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_context},
            ],
            "max_completion_tokens": 1500,
        }
        kwargs["response_format"] = self._response_format()

        response = await self.groq_client.chat.completions.create(**kwargs)
        try:
            content = response.choices[0].message.content
        except (AttributeError, IndexError, TypeError):
            return ""
        return content if isinstance(content, str) else ""

    def _system_prompt(self, *, correction: bool, has_failed_constraints: bool) -> str:
        system_prompt = SYSTEM_PROMPT
        if has_failed_constraints:
            system_prompt += "\n\n" + FAILED_ACTION_CONSTRAINT_PROMPT
        if correction:
            system_prompt += (
                "\n\nYour previous output failed validation or made an unsupported resolution claim. "
                "Return a corrected object matching the response schema. Do not make any resolution claim "
                "unless the current customer message explicitly confirms it."
            )
            if has_failed_constraints:
                system_prompt += "\n\n" + FAILED_ACTION_CORRECTION_PROMPT
        return system_prompt

    def _select_memories(
        self,
        memories: list[dict[str, Any]],
        *,
        current_message: str,
        authorized_business_context: str,
        failed_action_ids: set[str],
    ) -> list[dict[str, Any]] | None:
        """Keep complete mandatory failures, then fit lower-priority context deterministically."""
        mandatory = [item for item in memories if self._is_mandatory_failure(item)]
        lower_priority = [item for item in memories if item not in mandatory]
        lower_priority = self._deduplicate_lower_priority(lower_priority)
        lower_priority.sort(key=lambda item: (_MEMORY_PRIORITY.get(item["provenance"], 99), item["id"]))

        selected = sorted(mandatory, key=lambda item: item["id"])
        system_prompt = self._system_prompt(
            correction=True,
            has_failed_constraints=bool(failed_action_ids),
        )

        def fits(candidate: list[dict[str, Any]]) -> bool:
            context = self._serialize_context(
                current_message=current_message,
                authorized_business_context=authorized_business_context,
                memories=candidate,
                failed_action_ids=failed_action_ids,
            )
            return self._estimated_request_bytes(system_prompt, context) <= self.settings.groq_context_budget_bytes

        if not fits(selected):
            return None
        lowest_allowed_priority = 99
        for memory in lower_priority:
            priority = _MEMORY_PRIORITY.get(memory["provenance"], 99)
            if priority > lowest_allowed_priority:
                break
            candidate = [*selected, memory]
            if fits(candidate):
                selected = candidate
            else:
                # Keep same-priority items eligible, but do not let a lower-ranked
                # memory displace a higher-ranked one that did not fit.
                lowest_allowed_priority = priority
        return selected

    @staticmethod
    def _is_mandatory_failure(memory: dict[str, Any]) -> bool:
        metadata = memory["metadata"]
        return (
            memory["provenance"] in {"failed_attempt", "customer_reported"}
            and metadata.get("reported_outcome") == "failed"
            and metadata.get("confirmation_source") == "customer_report"
            and metadata.get("independently_verified") == "false"
            and "confirmation:customer_report" in memory["tags"]
        )

    @staticmethod
    def _failed_action_ids_from_memory(memory: dict[str, Any]) -> set[str]:
        if not SupportAgent._is_mandatory_failure(memory):
            return set()
        raw_ids = memory["metadata"].get("action_ids") or memory["metadata"].get("reported_action_ids") or ""
        if isinstance(raw_ids, str):
            return {action_id.strip() for action_id in raw_ids.split(",") if action_id.strip()}
        if isinstance(raw_ids, (list, tuple, set)) and all(isinstance(item, str) for item in raw_ids):
            return {action_id.strip() for action_id in raw_ids if action_id.strip()}
        return set()

    @staticmethod
    def _serialize_context(
        *,
        current_message: str,
        authorized_business_context: str,
        memories: list[dict[str, Any]],
        failed_action_ids: set[str],
    ) -> str:
        # Recall normalization keeps every representation for conflict detection and
        # auditability. Those duplicate provider representations are not useful to
        # the model and can multiply the same provenance metadata in the prompt.
        # Project selected records to the fields needed for support reasoning;
        # full normalized records remain available to validation and logging.
        prompt_memories = [SupportAgent._prompt_memory(item) for item in memories]
        conversation = json.loads(build_user_context(
            current_message=current_message,
            authorized_business_context=authorized_business_context,
            memories=prompt_memories,
        ))
        if not failed_action_ids:
            return json.dumps(conversation, ensure_ascii=False, separators=(",", ":"))
        return json.dumps(
            {
                "conversation": conversation,
                "failed_action_constraints": sorted(failed_action_ids),
                "constraint_provenance": "customer-reported, not independently verified",
            },
            ensure_ascii=False,
            separators=(",", ":"),
        )

    @staticmethod
    def _prompt_memory(memory: dict[str, Any]) -> dict[str, Any]:
        """Return a compact model view without dropping mandatory failure evidence."""
        if not SupportAgent._is_mandatory_failure(memory):
            # Optional facts retain their existing semantics; the selector may
            # remove them as complete items when the context budget is tight.
            projected = {
                "id": memory["id"],
                "text": memory["text"],
                "provenance": memory["provenance"],
                "metadata": memory["metadata"],
                "tags": memory["tags"],
            }
            if "duplicate_ids" in memory:
                projected["duplicate_ids"] = memory["duplicate_ids"]
            if "safety_conflict" in memory:
                projected["safety_conflict"] = memory["safety_conflict"]
            return projected

        metadata = memory["metadata"]
        keys = (
            "provenance_kind",
            "reported_outcome",
            "confirmation_source",
            "independently_verified",
            "action_ids",
            "reported_action_ids",
            "linked_to_prior_recommendation",
            "prior_recommendation_message_id",
            "original_customer_statement",
        )
        compact_metadata = {key: metadata[key] for key in keys if key in metadata}
        tags = [
            tag for tag in memory["tags"]
            if tag.startswith(("provenance:", "confirmation:", "outcome:", "action:"))
        ]
        return {
            "id": memory["id"],
            "text": memory["text"],
            "provenance": memory["provenance"],
            "metadata": compact_metadata,
            "tags": tags,
            "duplicate_ids": memory.get("duplicate_ids", []),
            "safety_conflict": memory.get("safety_conflict", False),
        }

    def _response_format(self) -> dict[str, Any]:
        if self.settings.groq_model in _STRICT_JSON_SCHEMA_MODELS:
            return {
                "type": "json_schema",
                "json_schema": {
                    "name": "support_agent_output",
                    "strict": True,
                    "schema": SUPPORT_AGENT_JSON_SCHEMA,
                },
            }
        return {"type": "json_object"}

    def _estimated_request_bytes(self, system_prompt: str, user_context: str) -> int:
        body = {
            "model": self.settings.groq_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_context},
            ],
            "max_completion_tokens": 1500,
            "response_format": self._response_format(),
        }
        serialized = json.dumps(body, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        return len(serialized) + _REQUEST_OVERHEAD_BYTES

    def _log_context_measurements(
        self,
        *,
        user_context: str,
        memories: list[dict[str, Any]],
        outcome: str,
        correlation_id: str,
        system_prompt: str = SYSTEM_PROMPT,
        selected_memories: list[dict[str, Any]] | None = None,
    ) -> None:
        text_by_provenance, metadata_by_provenance = self._memory_byte_totals(memories)
        selected_text_by_provenance, selected_metadata_by_provenance = self._memory_byte_totals(
            [self._prompt_memory(item) for item in (selected_memories or [])]
        )

        response_format = self._response_format()
        schema_bytes = len(json.dumps(response_format, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))
        system_bytes = len(system_prompt.encode("utf-8"))
        context_bytes = len(user_context.encode("utf-8"))
        selected_count = len(selected_memories) if selected_memories is not None else 0
        _CONTEXT_SIZE_LOGGER.info(
            "groq_context_size outcome=%s correlation_id=%s system_prompt_bytes=%d "
            "user_context_bytes=%d response_schema_bytes=%d estimated_request_bytes=%d "
            "recalled_memories=%d selected_memories=%d memory_text_bytes_by_provenance=%s "
            "memory_metadata_bytes_by_provenance=%s selected_memory_text_bytes_by_provenance=%s "
            "selected_memory_metadata_bytes_by_provenance=%s",
            outcome,
            correlation_id,
            system_bytes,
            context_bytes,
            schema_bytes,
            self._estimated_request_bytes(system_prompt, user_context),
            len(memories),
            selected_count,
            json.dumps(text_by_provenance, sort_keys=True, separators=(",", ":")),
            json.dumps(metadata_by_provenance, sort_keys=True, separators=(",", ":")),
            json.dumps(selected_text_by_provenance, sort_keys=True, separators=(",", ":")),
            json.dumps(selected_metadata_by_provenance, sort_keys=True, separators=(",", ":")),
        )

    @staticmethod
    def _memory_byte_totals(
        memories: list[dict[str, Any]],
    ) -> tuple[dict[str, int], dict[str, int]]:
        text_totals: dict[str, int] = {}
        metadata_totals: dict[str, int] = {}
        for memory in memories:
            provenance = memory["provenance"]
            represented_texts = [memory["text"]]
            representations = memory.get("source_representations", [])
            represented_texts.extend(
                representation["text"]
                for representation in representations
                if isinstance(representation.get("text"), str)
            )
            text_size = sum(len(text.encode("utf-8")) for text in represented_texts)
            text_totals[provenance] = text_totals.get(provenance, 0) + text_size
            metadata_values = [memory["metadata"]]
            metadata_values.extend(
                representation["metadata"]
                for representation in representations
                if isinstance(representation.get("metadata"), dict)
            )
            metadata_size = sum(
                len(json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))
                for value in metadata_values
            )
            metadata_totals[provenance] = metadata_totals.get(provenance, 0) + metadata_size
        return text_totals, metadata_totals

    @staticmethod
    def _deduplicate_lower_priority(memories: list[dict[str, Any]]) -> list[dict[str, Any]]:
        deduplicated: dict[str, dict[str, Any]] = {}
        for memory in memories:
            signature = json.dumps(
                {
                    "text": memory["text"],
                    "provenance": memory["provenance"],
                    "metadata": memory["metadata"],
                    "tags": memory["tags"],
                    "source_representations": memory.get("source_representations", []),
                },
                sort_keys=True,
                ensure_ascii=False,
                separators=(",", ":"),
            )
            existing = deduplicated.get(signature)
            if existing is None:
                deduplicated[signature] = {**memory, "duplicate_ids": []}
            else:
                existing["duplicate_ids"].append(memory["id"])
        return list(deduplicated.values())

    @staticmethod
    def _budget_escalation(
        memory_retrieved: bool,
        correlation_id: str,
        *,
        outcome: str = "context_budget_overflow",
    ) -> SupportAgentOutput:
        logger.warning(
            "support_agent_context_escalation outcome=%s correlation_id=%s",
            outcome,
            correlation_id,
        )
        provenance_conflict = outcome == "provenance_conflict"
        return SupportAgentOutput(
            response=(
                "I need a support specialist to review the troubleshooting history before I suggest another step."
            ),
            sentiment="unknown",
            memories_used=[],
            memory_retrieved=memory_retrieved,
            escalation_required=True,
            escalation_reason=(
                "Memory provenance could not be reconciled safely."
                if provenance_conflict
                else "Required context exceeded the safe response budget."
            ),
            interaction_summary=(
                "The interaction was escalated because memory provenance conflicted."
                if provenance_conflict
                else "The interaction was escalated because required context could not fit safely."
            ),
            suggested_memory_facts=[],
        )

    @staticmethod
    def _memory_context(recall_result: Any) -> list[dict[str, Any]]:
        # The installed Hindsight SDK exposes metadata and tags on RecallResult.
        # Keep these structured fields with the text to preserve provenance.
        results = getattr(recall_result, "results", None)
        source_facts = getattr(recall_result, "source_facts", None)
        if isinstance(recall_result, dict):
            results = recall_result.get("results")
            source_facts = recall_result.get("source_facts")
        if not isinstance(results, (list, tuple)):
            results = []
        if isinstance(source_facts, dict):
            results = [*results, *source_facts.values()]
        grouped: dict[str, list[dict[str, Any]]] = {}
        for result in results:
            if isinstance(result, dict):
                memory_id, text = result.get("id"), result.get("text")
                metadata, tags = result.get("metadata"), result.get("tags")
            else:
                memory_id, text = getattr(result, "id", None), getattr(result, "text", None)
                metadata, tags = getattr(result, "metadata", None), getattr(result, "tags", None)
            if isinstance(memory_id, str) and isinstance(text, str) and text.strip():
                safe_metadata = metadata if isinstance(metadata, dict) else {}
                safe_tags = [tag for tag in tags if isinstance(tag, str)] if isinstance(tags, list) else []
                provenance = safe_metadata.get("provenance_kind")
                if not isinstance(provenance, str) or provenance not in _PROVENANCE_LABELS:
                    provenance = "unclassified_historical_memory"
                grouped.setdefault(memory_id, []).append({
                    "id": memory_id,
                    "text": text,
                    "provenance": provenance,
                    "metadata": safe_metadata,
                    "tags": safe_tags,
                })
        return [SupportAgent._merge_memory_representations(memory_id, representations)
                for memory_id, representations in sorted(grouped.items())]

    @staticmethod
    def _merge_memory_representations(
        memory_id: str, representations: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Merge same-ID recall forms; ambiguous failure provenance escalates closed."""
        unique: dict[str, dict[str, Any]] = {}
        for representation in representations:
            fingerprint = json.dumps(
                representation, sort_keys=True, ensure_ascii=False, separators=(",", ":")
            )
            unique.setdefault(fingerprint, representation)
        ordered = [unique[key] for key in sorted(unique)]
        mandatory = [item for item in ordered if SupportAgent._is_mandatory_failure(item)]
        failure_signals = [item for item in ordered if SupportAgent._has_failure_signal(item)]

        conflict = False
        if mandatory:
            reference = SupportAgent._mandatory_provenance_signature(mandatory[0])
            if any(SupportAgent._mandatory_provenance_signature(item) != reference for item in mandatory[1:]):
                conflict = True
            for item in ordered:
                metadata = item["metadata"]
                provenance = metadata.get("provenance_kind")
                if provenance is not None and provenance not in {"failed_attempt", "customer_reported"}:
                    conflict = True
                provenance_tags = {
                    tag.split(":", 1)[1]
                    for tag in item["tags"]
                    if tag.startswith("provenance:")
                }
                if provenance_tags - {"failed_attempt", "customer_reported"}:
                    conflict = True
                if metadata.get("reported_outcome") not in (None, "failed"):
                    conflict = True
                if metadata.get("confirmation_source") not in (None, "customer_report"):
                    conflict = True
                if metadata.get("independently_verified") not in (None, "false"):
                    conflict = True
                confirmation_tags = {
                    tag.split(":", 1)[1]
                    for tag in item["tags"]
                    if tag.startswith("confirmation:")
                }
                if confirmation_tags - {"customer_report"}:
                    conflict = True
                outcome_tags = {
                    tag.split(":", 1)[1]
                    for tag in item["tags"]
                    if tag.startswith("outcome:")
                }
                if outcome_tags - {"reported_failed", "failed"}:
                    conflict = True
                action_ids = metadata.get("action_ids") or metadata.get("reported_action_ids")
                if action_ids is not None:
                    action_values = [
                        metadata[key]
                        for key in ("action_ids", "reported_action_ids")
                        if metadata.get(key) is not None
                    ]
                    normalized_action_values = {
                        SupportAgent._normalize_action_ids(value) for value in action_values
                    }
                    signature = SupportAgent._mandatory_provenance_signature(item)
                    if len(normalized_action_values) > 1 or signature[3] != reference[3]:
                        conflict = True
        elif failure_signals and len(ordered) > 1:
            # Incomplete failure-shaped provenance is not promoted to a mandatory
            # fact. If multiple same-ID representations disagree, fail closed.
            conflict = True

        primary = mandatory[0] if mandatory else ordered[0]
        merged_tags = sorted({tag for item in ordered for tag in item["tags"]})
        merged = {
            **primary,
            "id": memory_id,
            "tags": merged_tags,
            "safety_conflict": conflict,
        }
        if len(ordered) > 1:
            merged["source_representations"] = ordered
        return merged

    @staticmethod
    def _has_failure_signal(memory: dict[str, Any]) -> bool:
        metadata = memory["metadata"]
        return (
            memory["provenance"] == "failed_attempt"
            or metadata.get("reported_outcome") == "failed"
            or "provenance:failed_attempt" in memory["tags"]
            or "outcome:reported_failed" in memory["tags"]
        )

    @staticmethod
    def _mandatory_provenance_signature(memory: dict[str, Any]) -> tuple[Any, ...]:
        metadata = memory["metadata"]
        action_ids = metadata.get("action_ids") or metadata.get("reported_action_ids") or ""
        return (
            metadata.get("reported_outcome"),
            metadata.get("confirmation_source"),
            metadata.get("independently_verified"),
            SupportAgent._normalize_action_ids(action_ids),
        )

    @staticmethod
    def _normalize_action_ids(value: Any) -> tuple[str, ...]:
        if isinstance(value, str):
            return tuple(sorted(part.strip() for part in value.split(",") if part.strip()))
        if isinstance(value, (list, tuple, set)) and all(isinstance(item, str) for item in value):
            return tuple(sorted(item.strip() for item in value if item.strip()))
        return ("<invalid-action-id-shape>",)

    @staticmethod
    def _customer_confirmed_resolution(current_message: str) -> bool:
        match = _CUSTOMER_CONFIRMED_RESOLUTION.search(current_message)
        if not match:
            return False
        preceding_text = current_message[max(0, match.start() - 24) : match.start()]
        return not _NEGATED_CONFIRMATION.search(preceding_text)
