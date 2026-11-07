import hashlib
import hmac
import logging
from typing import Any, Literal
from uuid import UUID

from pydantic import SecretStr

from hindsight_client import Hindsight

logger = logging.getLogger(__name__)
SubjectType = Literal["customer", "visitor"]


class MemoryServiceError(Exception):
    status_code = 503
    public_message = "Customer memory service is temporarily unavailable"


class BankCreationError(MemoryServiceError):
    pass


class MemoryRetentionError(MemoryServiceError):
    pass


class MemoryRetrievalError(MemoryServiceError):
    pass


class ReflectionError(MemoryServiceError):
    pass


class MemoryService:
    """Workspace-scoped memory operations using keyed, namespaced opaque bank IDs."""

    def __init__(self, client: Hindsight, *, bank_id_secret: SecretStr | str, bank_prefix: str = "recall") -> None:
        self.client = client
        self.bank_prefix = bank_prefix
        self._bank_id_secret = (
            bank_id_secret.get_secret_value() if isinstance(bank_id_secret, SecretStr) else bank_id_secret
        )
        if not self._bank_id_secret:
            raise ValueError("A dedicated Hindsight bank ID secret is required")

    @staticmethod
    def _canonical_subject_id(subject_id: str, subject_type: SubjectType) -> str:
        if "@" in subject_id:
            raise ValueError("Email-shaped identifiers cannot be used for Hindsight memory")
        try:
            return str(UUID(subject_id))
        except (ValueError, AttributeError) as exc:
            kind = "customer" if subject_type == "customer" else "visitor"
            raise ValueError(f"{kind} memory requires an opaque UUID identifier") from exc

    def bank_id(self, workspace_id: str, subject_id: str, *, subject_type: SubjectType) -> str:
        if not isinstance(workspace_id, str) or not workspace_id.strip():
            raise ValueError("Workspace identity is required")
        canonical_id = self._canonical_subject_id(subject_id, subject_type)
        message = "\0".join(("workspace", workspace_id, "subject", subject_type, canonical_id)).encode("utf-8")
        digest = hmac.new(self._bank_id_secret.encode("utf-8"), message, hashlib.sha256).hexdigest()
        return f"{self.bank_prefix}-{digest}"

    async def ensure_bank(self, workspace_id: str, subject_id: str, *, subject_type: SubjectType) -> str:
        bank_id = self.bank_id(workspace_id, subject_id, subject_type=subject_type)
        try:
            # Installed SDK documents acreate_bank as create-or-update, so repeat calls are idempotent.
            await self.client.acreate_bank(
                bank_id=bank_id,
                name="RECALL AI customer support memory",
                retain_mission=(
                    "Distinguish customer-reported problems, attempted troubleshooting, failed attempts, "
                    "successful fixes, preferences, confirmed resolutions, unresolved issues, and escalation commitments. "
                    "Never infer resolution without customer confirmation."
                ),
                background="Support memory scoped to one workspace and one customer or anonymous visitor.",
            )
        except Exception:
            raise BankCreationError() from None
        return bank_id

    async def retain_memory(
        self,
        workspace_id: str,
        subject_id: str,
        content: str,
        *,
        subject_type: SubjectType,
        context: str | None = None,
        metadata: dict[str, str] | None = None,
        tags: list[str] | None = None,
        document_id: str | None = None,
        update_mode: Literal["replace", "append"] | None = None,
    ) -> Any:
        bank_id = await self.ensure_bank(workspace_id, subject_id, subject_type=subject_type)
        safe_metadata = dict(metadata or {})
        safe_metadata["workspace_scope"] = hashlib.sha256(workspace_id.encode()).hexdigest()[:16]
        try:
            result = await self.client.aretain(
                bank_id=bank_id,
                content=content,
                context=context,
                metadata=safe_metadata,
                tags=tags,
                document_id=document_id,
                update_mode=update_mode,
            )
            if getattr(result, "success", True) is False or (
                isinstance(result, dict) and result.get("success") is False
            ):
                raise MemoryRetentionError()
            return result
        except MemoryRetentionError:
            logger.error("Hindsight memory retention failed")
            raise
        except Exception:
            logger.error("Hindsight memory retention failed")
            raise MemoryRetentionError() from None

    async def recall_memories(
        self,
        workspace_id: str,
        subject_id: str,
        query: str,
        *,
        subject_type: SubjectType,
        tags: list[str] | None = None,
        tags_match: Literal["any", "all", "any_strict", "all_strict", "exact"] = "any",
    ) -> Any:
        bank_id = await self.ensure_bank(workspace_id, subject_id, subject_type=subject_type)
        try:
            return await self.client.arecall(
                bank_id=bank_id,
                query=query,
                include_source_facts=True,
                tags=tags,
                tags_match=tags_match,
            )
        except Exception:
            raise MemoryRetrievalError() from None

    async def reflect_memory(
        self, workspace_id: str, subject_id: str, query: str, *, subject_type: SubjectType
    ) -> Any:
        bank_id = await self.ensure_bank(workspace_id, subject_id, subject_type=subject_type)
        try:
            return await self.client.areflect(bank_id=bank_id, query=query)
        except Exception:
            raise ReflectionError() from None
