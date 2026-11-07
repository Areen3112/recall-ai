import logging
import re
from datetime import datetime
from typing import Any

from supabase import AsyncClient

from app.core.security import VerifiedIdentity
from app.core.performance import current_correlation_id

logger = logging.getLogger(__name__)
_SAFE_DATABASE_CODE = re.compile(r"(?:[0-9A-Z]{5}|PGRST[0-9]{3})\Z")


def _log_database_operation_failure(operation: str, error: Exception | None = None) -> None:
    """Log only static operation labels and safe provider diagnostic codes."""
    status = getattr(error, "status_code", None) if error is not None else None
    if not (isinstance(status, int) and not isinstance(status, bool) and 100 <= status <= 599):
        response = getattr(error, "response", None) if error is not None else None
        status = getattr(response, "status_code", None)
    if not (isinstance(status, int) and not isinstance(status, bool) and 100 <= status <= 599):
        status = "unavailable"
    raw_code = getattr(error, "code", None) if error is not None else None
    database_code = raw_code if isinstance(raw_code, str) and _SAFE_DATABASE_CODE.fullmatch(raw_code) else "unavailable"
    logger.warning(
        "database_operation_failed operation=%s exception_class=%s status=%s database_code=%s correlation_id=%s",
        operation,
        type(error).__name__ if error is not None else "RepositoryInvariantError",
        status,
        database_code,
        current_correlation_id() or "unavailable",
    )


class ChatRepositoryError(Exception):
    status_code = 503
    public_message = "Database service is temporarily unavailable"


class WorkspaceNotFoundError(ChatRepositoryError):
    status_code = 404
    public_message = "Workspace not found"


class CustomerNotFoundError(ChatRepositoryError):
    status_code = 404
    public_message = "Customer not found"


class InvalidSessionError(ChatRepositoryError):
    status_code = 400
    public_message = "Invalid chat session"


class IdempotencyConflictError(ChatRepositoryError):
    status_code = 409
    public_message = "Idempotency key was already used for a different message"


class ChatRepository:
    """Async workspace-scoped operations for the existing RECALL AI schema."""

    def __init__(self, client: AsyncClient) -> None:
        self.client = client

    async def resolve_workspace(self, public_id: str) -> dict[str, Any]:
        # public_id is the only workspace identifier available before resolution.
        try:
            response = await (
                self.client.table("workspaces")
                .select("id,public_id")
                .eq("public_id", public_id)
                .limit(2)
                .execute()
            )
        except Exception:
            raise ChatRepositoryError() from None
        row = self._single_row(response.data)
        if row is None:
            raise WorkspaceNotFoundError()
        return row

    async def resolve_customer(self, workspace_id: str, customer_id: str) -> dict[str, Any]:
        try:
            response = await (
                self.client.table("customers")
                .select("id,workspace_id,total_conversations,identity_verified")
                .eq("workspace_id", workspace_id)
                .eq("id", customer_id)
                .limit(2)
                .execute()
            )
        except Exception:
            raise ChatRepositoryError() from None
        row = self._single_row(response.data)
        if row is None or row.get("workspace_id") != workspace_id:
            raise CustomerNotFoundError()
        return row

    async def get_or_create_conversation(
        self,
        *,
        workspace_id: str,
        identity: VerifiedIdentity,
        session_id: str,
    ) -> tuple[dict[str, Any], bool]:
        customer_id = identity.subject_id if identity.identity_type == "customer" else None
        visitor_id = identity.subject_id if identity.identity_type == "visitor" else None
        try:
            existing = await self._find_session(workspace_id, session_id)
        except Exception:
            raise ChatRepositoryError() from None
        if existing is not None:
            self._validate_conversation_identity(existing, workspace_id, customer_id, visitor_id)
            if existing.get("status") not in {"open", "pending"}:
                raise InvalidSessionError()
            return existing, False

        payload = {
            "workspace_id": workspace_id,
            "customer_id": customer_id,
            "visitor_id": visitor_id,
            "session_id": session_id,
            "status": "open",
            "sentiment": "unknown",
        }
        try:
            response = await self.client.table("conversations").insert(payload).select(
                "id,workspace_id,customer_id,visitor_id,session_id,status,sentiment"
            ).execute()
            row = self._single_row(response.data)
            if row is None:
                raise RuntimeError("Conversation insert returned no row")
            self._validate_conversation_identity(row, workspace_id, customer_id, visitor_id)
            return row, True
        except InvalidSessionError:
            raise
        except Exception:
            # A concurrent request may have won the unique (workspace_id, session_id) race.
            try:
                existing = await self._find_session(workspace_id, session_id)
            except Exception:
                raise ChatRepositoryError() from None
            if existing is not None:
                self._validate_conversation_identity(existing, workspace_id, customer_id, visitor_id)
                if existing.get("status") in {"open", "pending"}:
                    return existing, False
            raise ChatRepositoryError() from None

    async def insert_message(
        self,
        *,
        workspace_id: str,
        conversation: dict[str, Any],
        identity: VerifiedIdentity,
        role: str,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        self._validate_conversation_identity(
            conversation,
            workspace_id,
            identity.subject_id if identity.identity_type == "customer" else None,
            identity.subject_id if identity.identity_type == "visitor" else None,
        )
        payload = {
            "workspace_id": workspace_id,
            "conversation_id": conversation["id"],
            "role": role,
            "content": content,
            "metadata": metadata or {},
        }
        try:
            response = await self.client.table("messages").insert(payload).select(
                "id,workspace_id,conversation_id,role,content,metadata,created_at"
            ).execute()
        except Exception as exc:
            key = (metadata or {}).get("idempotency_key")
            if isinstance(key, str):
                existing = await self.find_idempotent_message(
                    workspace_id=workspace_id,
                    conversation_id=conversation["id"],
                    role=role,
                    idempotency_key=key,
                )
                if existing is not None:
                    if role == "customer" and existing.get("content") != content:
                        raise IdempotencyConflictError() from None
                    return existing
            _log_database_operation_failure("messages.insert", exc)
            raise ChatRepositoryError() from None
        row = self._single_row(response.data)
        if row is None or row.get("workspace_id") != workspace_id or row.get("conversation_id") != conversation["id"]:
            _log_database_operation_failure("messages.insert_result")
            raise ChatRepositoryError() from None
        return row

    async def find_idempotent_message(
        self, *, workspace_id: str, conversation_id: str, role: str, idempotency_key: str
    ) -> dict[str, Any] | None:
        try:
            response = await (
                self.client.table("messages")
                .select("id,workspace_id,conversation_id,role,content,metadata,created_at")
                .eq("workspace_id", workspace_id)
                .eq("conversation_id", conversation_id)
                .eq("role", role)
                .contains("metadata", {"idempotency_key": idempotency_key})
                .limit(2)
                .execute()
            )
        except Exception as exc:
            _log_database_operation_failure("messages.idempotency_lookup", exc)
            raise ChatRepositoryError() from None
        row = self._single_row(response.data)
        if row is not None and (
            row.get("workspace_id") != workspace_id or row.get("conversation_id") != conversation_id
        ):
            raise ChatRepositoryError() from None
        return row

    async def find_prior_assistant_message(
        self, *, workspace_id: str, conversation_id: str, before_created_at: str
    ) -> dict[str, Any] | None:
        """Fetch the most recent persisted assistant response before a customer turn."""
        try:
            response = await (
                self.client.table("messages")
                .select("id,workspace_id,conversation_id,role,content,created_at")
                .eq("workspace_id", workspace_id)
                .eq("conversation_id", conversation_id)
                .eq("role", "assistant")
                .lt("created_at", before_created_at)
                .order("created_at", desc=True)
                .limit(1)
                .execute()
            )
        except Exception:
            raise ChatRepositoryError() from None
        row = self._single_row(response.data)
        if row is not None and (
            row.get("workspace_id") != workspace_id
            or row.get("conversation_id") != conversation_id
            or row.get("role") != "assistant"
        ):
            raise ChatRepositoryError()
        return row

    async def update_message_metadata(
        self, *, workspace_id: str, conversation_id: str, message_id: str, metadata: dict[str, Any]
    ) -> None:
        try:
            response = await (
                self.client.table("messages")
                .update({"metadata": metadata})
                .eq("workspace_id", workspace_id)
                .eq("conversation_id", conversation_id)
                .eq("id", message_id)
                .select("id,workspace_id,conversation_id")
                .execute()
            )
        except Exception:
            raise ChatRepositoryError() from None
        row = self._single_row(response.data)
        if row is None or row.get("workspace_id") != workspace_id or row.get("conversation_id") != conversation_id:
            raise ChatRepositoryError() from None

    async def update_conversation(
        self,
        *,
        workspace_id: str,
        conversation_id: str,
        sentiment: str,
        last_message_at: datetime,
    ) -> None:
        try:
            response = await (
                self.client.table("conversations")
                .update({"sentiment": sentiment, "last_message_at": last_message_at.isoformat()})
                .eq("workspace_id", workspace_id)
                .eq("id", conversation_id)
                .select("id,workspace_id")
                .execute()
            )
        except Exception as exc:
            _log_database_operation_failure("conversations.update", exc)
            raise ChatRepositoryError() from None
        row = self._single_row(response.data)
        if row is None or row.get("workspace_id") != workspace_id:
            _log_database_operation_failure("conversations.update_result")
            raise ChatRepositoryError() from None

    async def update_customer_interaction(
        self, *, workspace_id: str, customer_id: str, last_interaction: datetime
    ) -> None:
        try:
            response = await (
                self.client.table("customers")
                .update({"last_interaction": last_interaction.isoformat(), "updated_at": last_interaction.isoformat()})
                .eq("workspace_id", workspace_id)
                .eq("id", customer_id)
                .select("id,workspace_id")
                .execute()
            )
        except Exception as exc:
            _log_database_operation_failure("customers.interaction_update", exc)
            raise ChatRepositoryError() from None
        row = self._single_row(response.data)
        if row is None or row.get("workspace_id") != workspace_id:
            _log_database_operation_failure("customers.interaction_update_result")
            raise ChatRepositoryError() from None

    async def create_escalation_ticket(
        self,
        *,
        workspace_id: str,
        conversation: dict[str, Any],
        identity: VerifiedIdentity,
    ) -> bool:
        customer_id = identity.subject_id if identity.identity_type == "customer" else None
        visitor_id = identity.subject_id if identity.identity_type == "visitor" else None
        self._validate_conversation_identity(conversation, workspace_id, customer_id, visitor_id)
        try:
            existing_response = await (
                self.client.table("support_tickets")
                .select("id,workspace_id,customer_id,conversation_id,status")
                .eq("workspace_id", workspace_id)
                .eq("conversation_id", conversation["id"])
                .in_("status", ["open", "in_progress", "waiting"])
                .limit(2)
                .execute()
            )
            for row in self._rows(existing_response.data):
                if (
                    row.get("workspace_id") == workspace_id
                    and row.get("conversation_id") == conversation["id"]
                    and row.get("customer_id") == customer_id
                    and row.get("status") in {"open", "in_progress", "waiting"}
                ):
                    return False
            await self.client.table("support_tickets").insert(
                {
                    "workspace_id": workspace_id,
                    "customer_id": customer_id,
                    "conversation_id": conversation["id"],
                    "subject": "Customer support escalation requested",
                    "description": "The support agent recommended human follow-up. Review the scoped conversation messages.",
                    "status": "open",
                    "priority": "medium",
                }
            ).execute()
            return True
        except Exception:
            # Under the proposed partial unique index, a concurrent ticket insert
            # collides here. Re-read the active ticket within the same tenant scope.
            try:
                raced = await (
                    self.client.table("support_tickets")
                    .select("id,workspace_id,customer_id,conversation_id,status")
                    .eq("workspace_id", workspace_id)
                    .eq("conversation_id", conversation["id"])
                    .in_("status", ["open", "in_progress", "waiting"])
                    .limit(2)
                    .execute()
                )
                for row in self._rows(raced.data):
                    if (
                        row.get("workspace_id") == workspace_id
                        and row.get("conversation_id") == conversation["id"]
                        and row.get("customer_id") == customer_id
                        and row.get("status") in {"open", "in_progress", "waiting"}
                    ):
                        return False
            except Exception:
                pass
            raise ChatRepositoryError() from None

    async def record_activity(
        self,
        *,
        workspace_id: str,
        conversation: dict[str, Any],
        identity: VerifiedIdentity,
        event_type: str,
        description: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        customer_id = identity.subject_id if identity.identity_type == "customer" else None
        visitor_id = identity.subject_id if identity.identity_type == "visitor" else None
        self._validate_conversation_identity(conversation, workspace_id, customer_id, visitor_id)
        try:
            response = await self.client.table("agent_activity").insert(
                {
                    "workspace_id": workspace_id,
                    "customer_id": customer_id,
                    "conversation_id": conversation["id"],
                    "event_type": event_type,
                    "description": description,
                    "metadata": metadata or {},
                }
            ).select("id,workspace_id,conversation_id").execute()
        except Exception as exc:
            _log_database_operation_failure("agent_activity.insert", exc)
            raise ChatRepositoryError() from None
        row = self._single_row(response.data)
        if row is None or row.get("workspace_id") != workspace_id or row.get("conversation_id") != conversation["id"]:
            _log_database_operation_failure("agent_activity.insert_result")
            raise ChatRepositoryError() from None

    async def _find_session(self, workspace_id: str, session_id: str) -> dict[str, Any] | None:
        response = await (
            self.client.table("conversations")
            .select("id,workspace_id,customer_id,visitor_id,session_id,status,sentiment")
            .eq("workspace_id", workspace_id)
            .eq("session_id", session_id)
            .limit(2)
            .execute()
        )
        return self._single_row(response.data)

    @staticmethod
    def _validate_conversation_identity(
        conversation: dict[str, Any],
        workspace_id: str,
        customer_id: str | None,
        visitor_id: str | None,
    ) -> None:
        if conversation.get("workspace_id") != workspace_id:
            raise InvalidSessionError()
        if customer_id is not None:
            matches = conversation.get("customer_id") == customer_id and conversation.get("visitor_id") is None
        else:
            matches = conversation.get("customer_id") is None and conversation.get("visitor_id") == visitor_id
        if not matches:
            raise InvalidSessionError()

    @staticmethod
    def _rows(data: Any) -> list[dict[str, Any]]:
        if isinstance(data, dict):
            return [data]
        if isinstance(data, list) and all(isinstance(row, dict) for row in data):
            return data
        return []

    @classmethod
    def _single_row(cls, data: Any) -> dict[str, Any] | None:
        rows = cls._rows(data)
        if len(rows) > 1:
            raise ChatRepositoryError()
        return rows[0] if rows else None
