import logging
import hashlib
from datetime import datetime, timezone
import re
from uuid import UUID, uuid4

from fastapi import HTTPException, Response

from app.agents.support_agent import SupportAgent
from app.core.config import Settings
from app.core.security import VerifiedIdentity, verify_identity_token, verify_visitor_token
from app.database.chat_repository import ChatRepository, CustomerNotFoundError
from app.memory.memory_service import MemoryService, MemoryServiceError
from app.schemas.chat import ChatRequest, ChatResponse
from app.schemas.agent import SupportAgentOutput
from app.core.performance import log_async_stage
from app.agents.troubleshooting_actions import (
    explicitly_reported_failed_action_ids,
    recommended_action_ids,
)

logger = logging.getLogger(__name__)
_PROVENANCE_LOGGER = logging.getLogger("uvicorn.error.memory_provenance")
_FAILURE_LANGUAGE = re.compile(
    r"\b(?:did not|didn't|does not|doesn't)\s+(?:help|work|resolve)\b|\bfailed\b",
    re.IGNORECASE,
)

class ChatWorkflow:
    def __init__(
        self,
        *,
        repository: ChatRepository,
        memory_service: MemoryService,
        support_agent: SupportAgent,
        settings: Settings,
    ) -> None:
        self.repository = repository
        self.memory_service = memory_service
        self.support_agent = support_agent
        self.settings = settings

    async def handle(
        self,
        *,
        public_workspace_id: str,
        request: ChatRequest,
        idempotency_key: str,
        http_response: Response | None = None,
    ) -> ChatResponse:
        # Random per-request correlation is safe to log and is not derived from
        # customer, visitor, workspace, message, or idempotency data.
        correlation_id = str(uuid4())
        if not re.fullmatch(r"[A-Za-z0-9._:-]{16,128}", idempotency_key):
            raise HTTPException(status_code=400, detail="Invalid idempotency key")
        try:
            canonical_public_id = str(UUID(public_workspace_id))
        except (ValueError, AttributeError) as exc:
            raise HTTPException(status_code=400, detail="Invalid workspace identifier") from exc

        async with log_async_stage("workspace_identity_resolution", correlation_id):
            workspace = await self.repository.resolve_workspace(canonical_public_id)
            workspace_id = workspace.get("id")
            if not isinstance(workspace_id, str):
                raise RuntimeError("Workspace record is invalid")

            if request.customer_id is not None:
                identity = verify_identity_token(
                    request.identity_token,
                    workspace_id=workspace_id,
                    expected_customer_id=request.customer_id,
                    settings=self.settings,
                )
            else:
                identity = verify_visitor_token(
                    request.identity_token,
                    workspace_id=workspace_id,
                    expected_visitor_id=request.visitor_id,
                    settings=self.settings,
                )

        if request.customer_id is not None:
            async with log_async_stage("customer_lookup", correlation_id):
                # Resolve only by internal id plus authenticated workspace. The browser ID
                # is usable only because it was matched to the signed token above.
                customer = await self.repository.resolve_customer(workspace_id, identity.subject_id)
                if (
                    customer.get("id") != identity.subject_id
                    or customer.get("workspace_id") != workspace_id
                    or customer.get("identity_verified") is not True
                ):
                    raise CustomerNotFoundError()

        async with log_async_stage("conversation_lookup_creation", correlation_id):
            conversation, is_new = await self.repository.get_or_create_conversation(
                workspace_id=workspace_id,
                identity=identity,
                session_id=request.session_id,
            )
        async with log_async_stage("customer_message_persistence", correlation_id):
            customer_message = await self.repository.find_idempotent_message(
                workspace_id=workspace_id,
                conversation_id=conversation["id"],
                role="customer",
                idempotency_key=idempotency_key,
            )
            if customer_message is not None and customer_message.get("content") != request.message:
                from app.database.chat_repository import IdempotencyConflictError
                raise IdempotencyConflictError()
            if customer_message is None:
                customer_message = await self.repository.insert_message(
                    workspace_id=workspace_id,
                    conversation=conversation,
                    identity=identity,
                    role="customer",
                    content=request.message,
                    metadata={
                        "source": "widget",
                        "identity_type": identity.identity_type,
                        "idempotency_key": idempotency_key,
                    },
                )
                await self.repository.record_activity(
                    workspace_id=workspace_id,
                    conversation=conversation,
                    identity=identity,
                    event_type="customer_message_received",
                    description="A customer message was received.",
                    metadata={"identity_type": identity.identity_type, "new_conversation": is_new},
                )

        async with log_async_stage("assistant_message_lookup", correlation_id):
            assistant_message = await self.repository.find_idempotent_message(
                workspace_id=workspace_id,
                conversation_id=conversation["id"],
                role="assistant",
                idempotency_key=idempotency_key,
            )
        if assistant_message is not None and (assistant_message.get("metadata") or {}).get("workflow_status") == "complete":
            return self._cached_response(request.session_id, assistant_message)

        reported_failed_action_ids = explicitly_reported_failed_action_ids(request.message)
        linked_failed_action_ids: set[str] = set()
        linked_recommendation_message_id: str | None = None
        failure_record_skip_reason = (
            "failure_action_not_identified" if _FAILURE_LANGUAGE.search(request.message) else None
        )
        if reported_failed_action_ids:
            if not customer_message.get("created_at"):
                failure_record_skip_reason = "customer_message_timestamp_missing"
            else:
                prior_assistant = await self.repository.find_prior_assistant_message(
                    workspace_id=workspace_id,
                    conversation_id=conversation["id"],
                    before_created_at=customer_message["created_at"],
                )
                if prior_assistant is None:
                    failure_record_skip_reason = "prior_recommendation_not_found"
                elif not isinstance(prior_assistant.get("content"), str):
                    failure_record_skip_reason = "prior_recommendation_content_unavailable"
                else:
                    linked_failed_action_ids = (
                        reported_failed_action_ids & recommended_action_ids(prior_assistant["content"])
                    )
                    if not linked_failed_action_ids:
                        failure_record_skip_reason = "prior_recommendation_action_mismatch"
                    elif not isinstance(prior_assistant.get("id"), str) or not prior_assistant["id"]:
                        linked_failed_action_ids.clear()
                        failure_record_skip_reason = "prior_recommendation_id_unavailable"
                    else:
                        linked_recommendation_message_id = prior_assistant["id"]

        if linked_failed_action_ids:
            _PROVENANCE_LOGGER.info(
                "failed_attempt_provenance outcome=linked correlation_id=%s",
                correlation_id,
            )
        elif failure_record_skip_reason is not None:
            _PROVENANCE_LOGGER.info(
                "failed_attempt_provenance outcome=creation_skipped reason=%s correlation_id=%s",
                failure_record_skip_reason,
                correlation_id,
            )

        escalation_pending = False
        if assistant_message is None:
            try:
                # The agent performs Hindsight recall before Groq generation.
                result = await self.support_agent.respond(
                    workspace_id=workspace_id,
                    identity=identity,
                    current_message=request.message,
                    authorized_business_context="",
                    correlation_id=correlation_id,
                    reported_failed_action_ids=reported_failed_action_ids,
                )
            except Exception as exc:
                await self._record_workflow_failure(workspace_id, conversation, identity, "agent_generation", exc)
                raise
        else:
            result = self._agent_result_from_message(assistant_message)

        now = datetime.now(timezone.utc)
        async with log_async_stage("assistant_message_persistence", correlation_id):
            if assistant_message is None:
                assistant_message = await self.repository.insert_message(
                    workspace_id=workspace_id,
                    conversation=conversation,
                    identity=identity,
                    role="assistant",
                    content=result.response,
                    metadata={
                        "idempotency_key": idempotency_key,
                        "workflow_status": "response_persisted",
                        "sentiment": result.sentiment,
                        "escalation_required": result.escalation_required,
                        "escalation_reason": result.escalation_reason,
                        "memory_retrieved": result.memory_retrieved,
                        "memories_used": result.memories_used,
                        "suggested_memory_facts": result.suggested_memory_facts,
                    },
                )
                # A concurrent request can win the unique assistant-message index.
                if assistant_message.get("content") != result.response:
                    result = self._agent_result_from_message(assistant_message)
            try:
                await self.repository.update_conversation(
                    workspace_id=workspace_id,
                    conversation_id=conversation["id"],
                    sentiment=result.sentiment,
                    last_message_at=now,
                )
                if identity.identity_type == "customer":
                    await self.repository.update_customer_interaction(
                        workspace_id=workspace_id,
                        customer_id=identity.subject_id,
                        last_interaction=now,
                    )
                await self.repository.record_activity(
                    workspace_id=workspace_id,
                    conversation=conversation,
                    identity=identity,
                    event_type="assistant_response_generated",
                    description="The support agent generated a response.",
                    metadata={
                        "sentiment": result.sentiment,
                        "memory_retrieved": result.memory_retrieved,
                        "escalation_required": result.escalation_required,
                    },
                )
            except Exception as exc:
                await self._record_workflow_failure(workspace_id, conversation, identity, "response_persistence", exc)
                raise
        if result.escalation_required:
            async with log_async_stage("escalation_ticket_handling", correlation_id) as mark_stage_failed:
                try:
                    ticket_created = await self.repository.create_escalation_ticket(
                        workspace_id=workspace_id,
                        conversation=conversation,
                        identity=identity,
                    )
                except Exception as exc:
                    mark_stage_failed()
                    escalation_pending = True
                    await self._record_workflow_failure(workspace_id, conversation, identity, "escalation", exc)
                    if http_response is not None:
                        http_response.status_code = 202
                        http_response.headers["X-Workflow-Status"] = "escalation-pending"
                    ticket_created = False
                try:
                    await self.repository.record_activity(
                        workspace_id=workspace_id,
                        conversation=conversation,
                        identity=identity,
                        event_type="escalation_recommended",
                        description="The support agent recommended human follow-up.",
                        metadata={"ticket_created": ticket_created},
                    )
                except Exception as exc:
                    await self._record_workflow_failure(workspace_id, conversation, identity, "escalation_activity", exc)
                    raise

        retention_failed = False
        try:
            async with log_async_stage("hindsight_memory_retention", correlation_id):
                await self._retain_provenance_records(
                    workspace_id=workspace_id,
                    identity=identity,
                    session_fingerprint=hashlib.sha256(request.session_id.encode("utf-8")).hexdigest(),
                    customer_message=request.message,
                    assistant_response=result.response,
                    suggestions=result.suggested_memory_facts,
                    reported_failed_action_ids=reported_failed_action_ids,
                    linked_failed_action_ids=linked_failed_action_ids,
                    linked_recommendation_message_id=linked_recommendation_message_id,
                    correlation_id=correlation_id,
                )
        except MemoryServiceError:
            retention_failed = True
            # The response and conversation are already durable. Do not turn retention
            # failure into a failed chat response or claim that memory was updated.
            logger.error("Hindsight retention failed after response persistence")
            try:
                await self.repository.record_activity(
                    workspace_id=workspace_id,
                    conversation=conversation,
                    identity=identity,
                    event_type="memory_retention_failed",
                    description="The interaction response was saved, but memory retention failed.",
                    metadata={"retention_status": "failed"},
                )
            except Exception:
                logger.error("Could not record memory retention failure activity")

        final_status = "escalation_pending" if escalation_pending else ("retention_failed" if retention_failed else "complete")
        final_metadata = dict(assistant_message.get("metadata") or {})
        final_metadata["workflow_status"] = final_status
        final_metadata["retention_status"] = "failed" if retention_failed else "stored"
        try:
            await self.repository.update_message_metadata(
                workspace_id=workspace_id,
                conversation_id=conversation["id"],
                message_id=assistant_message["id"],
                metadata=final_metadata,
            )
        except Exception as exc:
            await self._record_workflow_failure(workspace_id, conversation, identity, "workflow_completion", exc)
            raise
        if http_response is not None:
            http_response.headers["X-Workflow-Status"] = final_status
            http_response.headers["X-Memory-Status"] = "failed" if retention_failed else "stored"
        return ChatResponse(
            response=result.response,
            session_id=request.session_id,
            sentiment=result.sentiment,
            memories_used=result.memories_used,
            memory_retrieved=result.memory_retrieved,
            escalation_required=result.escalation_required,
            escalation_reason=result.escalation_reason or None,
        )

    async def _record_workflow_failure(
        self, workspace_id: str, conversation: dict, identity: VerifiedIdentity, stage: str, exc: Exception
    ) -> None:
        try:
            await self.repository.record_activity(
                workspace_id=workspace_id,
                conversation=conversation,
                identity=identity,
                event_type="workflow_stage_failed",
                description="A chat workflow stage failed and may require retry.",
                metadata={"stage": stage, "error_type": type(exc).__name__},
            )
        except Exception:
            logger.error("Could not record chat workflow failure")

    @staticmethod
    def _agent_result_from_message(message: dict) -> SupportAgentOutput:
        metadata = message.get("metadata") or {}
        return SupportAgentOutput(
            response=message["content"],
            sentiment=metadata.get("sentiment", "unknown"),
            memories_used=metadata.get("memories_used", []),
            memory_retrieved=metadata.get("memory_retrieved", False),
            escalation_required=metadata.get("escalation_required", False),
            escalation_reason=metadata.get("escalation_reason", ""),
            interaction_summary="Resumed persisted response.",
            suggested_memory_facts=metadata.get("suggested_memory_facts", []),
        )

    @classmethod
    def _cached_response(cls, session_id: str, message: dict) -> ChatResponse:
        result = cls._agent_result_from_message(message)
        return ChatResponse(
            response=result.response,
            session_id=session_id,
            sentiment=result.sentiment,
            memories_used=result.memories_used,
            memory_retrieved=result.memory_retrieved,
            escalation_required=result.escalation_required,
            escalation_reason=result.escalation_reason or None,
        )

    async def _retain_provenance_records(
        self,
        *,
        workspace_id: str,
        identity: VerifiedIdentity,
        session_fingerprint: str,
        customer_message: str,
        assistant_response: str,
        suggestions: list[str],
        reported_failed_action_ids: set[str] | None = None,
        linked_failed_action_ids: set[str] | None = None,
        linked_recommendation_message_id: str | None = None,
        correlation_id: str,
    ) -> None:
        """Persist each trust class separately with SDK-supported metadata and tags."""
        reported_failed_action_ids = reported_failed_action_ids or set()
        linked_failed_action_ids = linked_failed_action_ids or set()
        customer_metadata = {
            "source": "chat_api",
            "identity_type": identity.identity_type,
            "session_fingerprint": session_fingerprint,
            "provenance_kind": "customer_reported",
            "suggestions_unverified": "false",
        }
        if reported_failed_action_ids:
            # This records only an explicit customer report. It does not assert the
            # action was recommended in this conversation.
            customer_metadata.update({
                "reported_outcome": "failed",
                "confirmation_source": "customer_report",
                "independently_verified": "false",
                "reported_action_ids": ",".join(sorted(reported_failed_action_ids)),
            })
        records = [
            ("customer_reported", customer_message, ["provenance:customer_reported"], customer_metadata),
            ("assistant_generated", assistant_response, ["provenance:assistant_generated"]),
            *[("model_suggestion", fact, ["provenance:model_suggestion", "suggestions:unverified"])
              for fact in suggestions],
        ]
        if linked_failed_action_ids:
            records.append((
                "failed_attempt",
                customer_message,
                ["provenance:failed_attempt", "outcome:reported_failed", "confirmation:customer_report"],
                {
                    "source": "chat_api",
                    "identity_type": identity.identity_type,
                    "session_fingerprint": session_fingerprint,
                    "provenance_kind": "failed_attempt",
                    "confirmation_source": "customer_report",
                    "independently_verified": "false",
                    "reported_outcome": "failed",
                    "action_ids": ",".join(sorted(linked_failed_action_ids)),
                    "linked_to_prior_recommendation": "true",
                    "prior_recommendation_message_id": linked_recommendation_message_id or "",
                    "customer_statement_sha256": hashlib.sha256(
                        customer_message.encode("utf-8")
                    ).hexdigest(),
                },
            ))
        for record in records:
            provenance_kind, content, tags = record[:3]
            record_metadata = record[3] if len(record) > 3 else None
            is_reported_outcome = provenance_kind == "failed_attempt"
            try:
                await self.memory_service.retain_memory(
                    workspace_id,
                    identity.subject_id,
                    content,
                    subject_type=identity.identity_type,
                    context=(
                        f"Provenance classification: {provenance_kind}. Model suggestions are never confirmed facts. "
                        "No issue is resolved without explicit customer confirmation."
                    ),
                    metadata=record_metadata or {
                        "source": "chat_api",
                        "identity_type": identity.identity_type,
                        "session_fingerprint": session_fingerprint,
                        "provenance_kind": provenance_kind,
                        "suggestions_unverified": "true" if provenance_kind == "model_suggestion" else "false",
                        **({
                            "confirmation_source": "customer_report",
                            "independently_verified": "false",
                            "reported_outcome": "failed",
                        } if is_reported_outcome else {}),
                    },
                    tags=[*tags, f"identity:{identity.identity_type}"],
                )
            except MemoryServiceError:
                if provenance_kind == "failed_attempt":
                    _PROVENANCE_LOGGER.error(
                        "failed_attempt_provenance outcome=retention_failure correlation_id=%s",
                        correlation_id,
                    )
                raise
            else:
                if provenance_kind == "failed_attempt":
                    _PROVENANCE_LOGGER.info(
                        "failed_attempt_provenance outcome=retention_success correlation_id=%s",
                        correlation_id,
                    )
