"""Development-only synthetic customer and Hindsight seed for Sarah Mitchell."""

import argparse
import asyncio
import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import UUID, uuid4

import jwt
from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))
load_dotenv(BACKEND_DIR / ".env")

from app.core.config import get_settings  # noqa: E402
from app.core.security import VerifiedIdentity  # noqa: E402
from app.database.chat_repository import ChatRepository  # noqa: E402
from app.database.supabase import close_supabase_client, create_supabase_client  # noqa: E402
from app.memory.hindsight_client import create_hindsight_client  # noqa: E402
from app.memory.memory_service import MemoryService  # noqa: E402


EXTERNAL_ID = "demo-sarah-mitchell-v1"
HISTORY_SESSION = "demo-sarah-history-v1"
HISTORY_MEMORY_DOCUMENT_ID = "synthetic-sarah-history-baseline-v1"
HISTORY_MEMORY_FIXTURE_ID = "sarah-history-baseline-v1"
HISTORY_MESSAGES = [
    ("customer", "My Bluetooth headphones disconnect about every 10 minutes."),
    ("customer", "I restarted Bluetooth and the headphones, but that did not help. I prefer step-by-step troubleshooting."),
    ("assistant", "I understand. We can try a different check one step at a time."),
]
DEMO_CONFIG_FILENAME = ".sarah_demo.json"
DASHBOARD_DEMO_CONFIG_FILENAME = ".sarah_dashboard_demo.json"
DASHBOARD_DEMO_STATE_FILENAME = f"{DASHBOARD_DEMO_CONFIG_FILENAME}.run.json"


def new_synthetic_customer_payload(workspace_id: str, customer_id: str | None = None) -> dict:
    """Build an isolated Sarah persona row with a fresh opaque internal UUID."""
    customer_id = str(UUID(customer_id)) if customer_id is not None else str(uuid4())
    return {
        "id": customer_id,
        "workspace_id": workspace_id,
        "external_id": f"{EXTERNAL_ID}:{customer_id}",
        "name": "Sarah Mitchell",
        # Email is nullable in the schema; omitting PII also avoids workspace email collisions.
        "email": None,
        "identity_verified": True,
        "total_conversations": 0,
    }


def history_session_id(customer_id: str) -> str:
    return f"{HISTORY_SESSION}-{str(UUID(customer_id))}"


def create_demo_identity_token(settings, workspace_id: str, customer_id: str, *, now=None) -> str:
    now = now or datetime.now(timezone.utc)
    lifetime = min(settings.identity_token_max_ttl_seconds, 900)
    return jwt.encode(
        {
            "exp": now + timedelta(seconds=lifetime),
            "iat": now,
            "iss": settings.identity_token_issuer,
            "aud": settings.identity_token_audience,
            "identity_type": "customer",
            "workspace_id": workspace_id,
            "customer_id": str(UUID(customer_id)),
        },
        settings.identity_token_secret.get_secret_value(),
        algorithm="HS256",
    )


def write_demo_config(path: Path, config: dict) -> None:
    """Atomically write private local config without exposing its signed token."""
    temporary_path = path.with_name(f".{path.name}.{uuid4().hex}.tmp")
    descriptor = os.open(temporary_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as demo_stream:
            json.dump(config, demo_stream, indent=2)
            demo_stream.flush()
            os.fsync(demo_stream.fileno())
        os.replace(temporary_path, path)
        os.chmod(path, 0o600)
    except Exception:
        try:
            os.close(descriptor)
        except OSError:
            pass
        temporary_path.unlink(missing_ok=True)
        raise


def write_sarah_demo_configs(
    backend_dir: Path,
    *,
    workspace_public_id: str,
    workspace_id: str,
    customer_id: str,
    identity_token: str,
) -> tuple[Path, Path]:
    """Write the CLI and dashboard configs after synthetic data setup succeeds."""
    cli_path = backend_dir / DEMO_CONFIG_FILENAME
    dashboard_path = backend_dir / DASHBOARD_DEMO_CONFIG_FILENAME
    write_demo_config(
        cli_path,
        {
            "workspace_public_id": workspace_public_id,
            "workspace_id": workspace_id,
            "customer_id": customer_id,
            "identity_token": identity_token,
            "demo_namespace": EXTERNAL_ID,
            "demo_run_id": customer_id,
            "run_status": "ready",
            "synthetic_data": True,
        },
    )
    write_demo_config(
        dashboard_path,
        {
            "workspace_public_id": workspace_public_id,
            "workspace_id": workspace_id,
            "customer_id": customer_id,
            "identity_token": identity_token,
            "demo_namespace": EXTERNAL_ID,
            "synthetic_data": True,
        },
    )
    # A fresh customer gets exactly one dashboard scenario run. The API records
    # that run ID so a browser replay cannot accumulate contradictory history in
    # this customer's otherwise isolated memory bank.
    write_demo_config(
        backend_dir / DASHBOARD_DEMO_STATE_FILENAME,
        {"customer_id": customer_id, "active_run_id": None},
    )
    return cli_path, dashboard_path


async def seed_history_memory_once(memory_service, workspace_id: str, customer_id: str) -> bool:
    """Append the immutable baseline once; never replace or delete prior memories."""
    tag = f"fixture:{HISTORY_MEMORY_FIXTURE_ID}"
    recall = await memory_service.recall_memories(
        workspace_id,
        customer_id,
        "Synthetic Sarah baseline historical Bluetooth troubleshooting and preferences",
        subject_type="customer",
        tags=["synthetic_demo", tag],
        tags_match="all_strict",
    )
    results = getattr(recall, "results", None)
    source_facts = getattr(recall, "source_facts", None)
    if isinstance(recall, dict):
        results = recall.get("results")
        source_facts = recall.get("source_facts")
    candidates = list(results) if isinstance(results, (list, tuple)) else []
    if isinstance(source_facts, dict):
        candidates.extend(source_facts.values())
    for item in candidates:
        metadata = item.get("metadata") if isinstance(item, dict) else getattr(item, "metadata", None)
        tags = item.get("tags") if isinstance(item, dict) else getattr(item, "tags", None)
        if (
            isinstance(metadata, dict)
            and metadata.get("fixture_id") == HISTORY_MEMORY_FIXTURE_ID
            and isinstance(tags, (list, tuple))
            and "synthetic_demo" in tags
            and tag in tags
        ):
            return False
    await memory_service.retain_memory(
        workspace_id,
        customer_id,
        (
            "Customer-reported problem: Bluetooth headphones disconnect about every 10 minutes.\n"
            "Customer-reported troubleshooting attempt: Restarting Bluetooth and the headphones.\n"
            "Customer-reported outcome: The restart did not help; it is a failed attempt.\n"
            "Customer preference: Step-by-step troubleshooting instructions.\n"
            "Resolution status: Unresolved; the customer has not confirmed a fix."
        ),
        subject_type="customer",
        context="Synthetic Sarah Mitchell development fixture; these statements are fictional demo data.",
        metadata={
            "source": "synthetic_demo_seed",
            "identity_type": "customer",
            "provenance": "fictional_customer_report",
            "fixture_id": HISTORY_MEMORY_FIXTURE_ID,
        },
        tags=["synthetic_demo", tag, "failed_attempt", "customer_preference", "unresolved"],
        document_id=HISTORY_MEMORY_DOCUMENT_ID,
        update_mode="append",
    )
    return True


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Seed synthetic Sarah Mitchell demo data (development only).")
    parser.add_argument("--workspace-public-id", required=True, help="Existing workspace public_id UUID")
    return parser.parse_args()


def validate_demo_target(settings) -> None:
    """Fail closed unless the configured Supabase project is an allowlisted demo."""
    if os.environ.get("APP_ENV") != "development":
        raise RuntimeError("APP_ENV must be explicitly set to development")
    if os.environ.get("ALLOW_SYNTHETIC_DEMO_SEED", "").lower() != "true":
        raise RuntimeError("ALLOW_SYNTHETIC_DEMO_SEED=true is required")
    expected_ref = settings.demo_supabase_project_ref
    allowlist = {
        item.strip()
        for item in settings.demo_supabase_project_allowlist.split(",")
        if item.strip()
    }
    if not expected_ref or not re.fullmatch(r"[a-z0-9-]+", expected_ref) or expected_ref not in allowlist:
        raise RuntimeError("Demo Supabase project reference is not allowlisted")
    if settings.supabase_url is None:
        raise RuntimeError("SUPABASE_URL must identify the approved demo project")
    hostname = settings.supabase_url.host
    match = re.fullmatch(r"([a-z0-9-]+)\.supabase\.co", hostname or "")
    if match is None or match.group(1) != expected_ref:
        raise RuntimeError("Configured Supabase URL does not match the approved demo project")


async def seed(workspace_public_id: str) -> None:
    settings = get_settings()
    validate_demo_target(settings)
    if not settings.identity_token_secret or not settings.identity_token_issuer or not settings.identity_token_audience:
        raise RuntimeError("Signed identity token configuration is incomplete")
    if not settings.hindsight_api_key or not settings.hindsight_bank_id_secret:
        raise RuntimeError("Hindsight demo configuration is incomplete")
    client = await create_supabase_client(settings)
    if client is None:
        raise RuntimeError("SUPABASE_SERVICE_ROLE_KEY is not configured")
    hindsight = create_hindsight_client(settings)
    if hindsight is None:
        await close_supabase_client(client)
        raise RuntimeError("HINDSIGHT_API_KEY is not configured")

    try:
        repository = ChatRepository(client)
        workspace = await repository.resolve_workspace(str(UUID(workspace_public_id)))
        workspace_id = workspace["id"]

        # Each seed creates a fresh customer subject. The deterministic HMAC bank ID
        # therefore selects an empty per-run bank while preserving tenant scoping.
        customer_payload = new_synthetic_customer_payload(workspace_id)
        customer_id = customer_payload["id"]
        customer_response = await (
            client.table("customers")
            .select("id,workspace_id,external_id,total_conversations,identity_verified")
            .eq("workspace_id", workspace_id)
            .eq("id", customer_id)
            .limit(2)
            .execute()
        )
        customers = repository._rows(customer_response.data)
        if len(customers) > 1:
            raise RuntimeError("Demo customer lookup was ambiguous")
        if customers:
            customer = customers[0]
            if customer.get("workspace_id") != workspace_id:
                raise RuntimeError("Demo customer is outside the selected workspace")
            if customer.get("external_id") != customer_payload["external_id"]:
                raise RuntimeError("Synthetic demo customer identifier did not match")
            if customer.get("identity_verified") is not True:
                raise RuntimeError("Synthetic demo customer identity is not verified")
        else:
            inserted = await client.table("customers").insert(
                customer_payload
            ).select("id,workspace_id,external_id,total_conversations,identity_verified").execute()
            customer = repository._single_row(inserted.data)
            if (
                customer is None
                or customer.get("id") != customer_id
                or customer.get("workspace_id") != workspace_id
                or customer.get("external_id") != customer_payload["external_id"]
                or customer.get("identity_verified") is not True
            ):
                raise RuntimeError("Demo customer could not be created")

        identity = VerifiedIdentity(
            workspace_id=workspace_id,
            identity_type="customer",
            subject_id=customer["id"],
        )
        conversation, created = await repository.get_or_create_conversation(
            workspace_id=workspace_id,
            identity=identity,
            session_id=history_session_id(customer["id"]),
        )
        message_response = await (
            client.table("messages")
            .select("role,content")
            .eq("workspace_id", workspace_id)
            .eq("conversation_id", conversation["id"])
            .execute()
        )
        existing_messages = {
            (row.get("role"), row.get("content")) for row in repository._rows(message_response.data)
        }
        for role, content in HISTORY_MESSAGES:
            if (role, content) not in existing_messages:
                await repository.insert_message(
                    workspace_id=workspace_id,
                    conversation=conversation,
                    identity=identity,
                    role=role,
                    content=content,
                    metadata={"source": "synthetic_demo_seed"},
                )
        if created:
            now = datetime.now(timezone.utc)
            conversation_count = max(int(customer.get("total_conversations") or 0), 1)
            await client.table("customers").update(
                {
                    "total_conversations": conversation_count,
                    "last_interaction": now.isoformat(),
                    "updated_at": now.isoformat(),
                }
            ).eq("workspace_id", workspace_id).eq("id", customer["id"]).execute()

        memory_service = MemoryService(hindsight, bank_id_secret=settings.hindsight_bank_id_secret)
        await seed_history_memory_once(memory_service, workspace_id, customer["id"])

        identity_token = create_demo_identity_token(settings, workspace_id, customer["id"])
        demo_file, dashboard_demo_file = write_sarah_demo_configs(
            BACKEND_DIR,
            workspace_public_id=workspace_public_id,
            workspace_id=workspace_id,
            customer_id=customer["id"],
            identity_token=identity_token,
        )
        print("Synthetic Sarah Mitchell seed is ready.")
        print(f"Demo configuration written to {demo_file} (ignored by git; token not printed).")
        print(f"Dashboard demo configuration written to {dashboard_demo_file} (token not printed).")
    finally:
        try:
            await hindsight.aclose()
        finally:
            await close_supabase_client(client)


def main() -> None:
    args = parse_args()
    try:
        asyncio.run(seed(args.workspace_public_id))
    except Exception as exc:
        # Never emit provider exception text, request data, or signed tokens.
        print(f"Sarah demo seed failed ({type(exc).__name__}).", file=sys.stderr)
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
