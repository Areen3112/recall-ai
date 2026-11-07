import json
import fcntl
import os
import re
from pathlib import Path
import tempfile
from uuid import UUID

from fastapi import APIRouter, Header, HTTPException, Request, Response

from app.schemas.chat import ChatRequest, ChatResponse
from app.schemas.demo import DashboardDemoChatRequest


router = APIRouter(prefix="/api/v1", tags=["Development Demo"])
DASHBOARD_DEMO_CONFIG_PATH = Path(__file__).resolve().parents[3] / ".sarah_dashboard_demo.json"
EXPECTED_DEMO_NAMESPACE = "demo-sarah-mitchell-v1"
_IDEMPOTENCY_KEY_PATTERN = re.compile(r"[A-Za-z0-9._:-]{16,128}")
_SESSION_PATTERN = re.compile(
    r"sarah-dashboard-(?P<run_id>[0-9a-fA-F-]{36})-(?:learning|recall)"
)


def _load_dashboard_demo_config(path: Path) -> dict:
    """Read and validate the private synthetic identity configuration fail-closed."""
    try:
        with path.open("r", encoding="utf-8") as config_file:
            config = json.load(config_file)
        if (
            not isinstance(config, dict)
            or set(config) != {
                "workspace_public_id", "workspace_id", "customer_id", "identity_token",
                "demo_namespace", "synthetic_data",
            }
            or config.get("synthetic_data") is not True
            or config.get("demo_namespace") != EXPECTED_DEMO_NAMESPACE
        ):
            raise ValueError
        for field in ("workspace_public_id", "workspace_id", "customer_id"):
            config[field] = str(UUID(config[field]))
        if not isinstance(config.get("identity_token"), str) or not config["identity_token"]:
            raise ValueError
        return config
    except (OSError, UnicodeError, json.JSONDecodeError, KeyError, TypeError, ValueError, AttributeError):
        raise HTTPException(status_code=503, detail="Dashboard demo is unavailable") from None


def _claim_dashboard_run(state_path: Path, *, customer_id: str, session_id: str) -> None:
    """Allow one browser run per freshly seeded customer, across its sessions."""
    match = _SESSION_PATTERN.fullmatch(session_id)
    if match is None:
        raise HTTPException(status_code=400, detail="Invalid demo session")
    try:
        run_id = str(UUID(match.group("run_id")))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid demo session") from None

    lock_path = state_path.with_name(f"{state_path.name}.lock")
    try:
        lock_fd = os.open(lock_path, os.O_CREAT | os.O_RDWR, 0o600)
    except OSError:
        raise HTTPException(status_code=503, detail="Dashboard demo is unavailable") from None
    try:
        os.fchmod(lock_fd, 0o600)
        fcntl.flock(lock_fd, fcntl.LOCK_EX)
        try:
            state = json.loads(state_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError):
            raise HTTPException(status_code=503, detail="Dashboard demo is unavailable") from None
        if not isinstance(state, dict) or state.get("customer_id") != customer_id:
            raise HTTPException(status_code=503, detail="Dashboard demo is unavailable")
        active_run_id = state.get("active_run_id")
        if active_run_id is not None and active_run_id != run_id:
            raise HTTPException(status_code=409, detail="Reseed the synthetic demo before starting another run")
        if active_run_id is None:
            state["active_run_id"] = run_id
            descriptor, temporary_name = tempfile.mkstemp(prefix=f".{state_path.name}.", dir=state_path.parent)
            temporary_path = Path(temporary_name)
            try:
                os.fchmod(descriptor, 0o600)
                with os.fdopen(descriptor, "w", encoding="utf-8") as state_file:
                    json.dump(state, state_file)
                    state_file.flush()
                    os.fsync(state_file.fileno())
                os.replace(temporary_path, state_path)
                os.chmod(state_path, 0o600)
            except Exception:
                try:
                    os.close(descriptor)
                except OSError:
                    pass
                temporary_path.unlink(missing_ok=True)
                raise HTTPException(status_code=503, detail="Dashboard demo is unavailable") from None
    finally:
        try:
            fcntl.flock(lock_fd, fcntl.LOCK_UN)
        finally:
            os.close(lock_fd)


@router.post("/demo/chat", response_model=ChatResponse)
async def dashboard_demo_chat(
    request_context: Request,
    http_response: Response,
    request: DashboardDemoChatRequest,
    idempotency_key: str = Header(..., alias="Idempotency-Key", min_length=16, max_length=128),
) -> ChatResponse:
    settings = getattr(request_context.app.state, "settings", None)
    if (
        settings is None
        or settings.app_env != "development"
        or settings.allow_synthetic_demo_seed is not True
    ):
        raise HTTPException(status_code=404, detail="Not found")
    if _IDEMPOTENCY_KEY_PATTERN.fullmatch(idempotency_key) is None:
        raise HTTPException(status_code=400, detail="Invalid idempotency key")

    config = _load_dashboard_demo_config(DASHBOARD_DEMO_CONFIG_PATH)
    _claim_dashboard_run(
        DASHBOARD_DEMO_CONFIG_PATH.with_name(f"{DASHBOARD_DEMO_CONFIG_PATH.name}.run.json"),
        customer_id=config["customer_id"],
        session_id=request.session_id,
    )
    workflow = getattr(request_context.app.state, "chat_workflow", None)
    if workflow is None:
        raise HTTPException(status_code=503, detail="Chat service is temporarily unavailable")

    chat_request = ChatRequest(
        customer_id=config["customer_id"],
        identity_token=config["identity_token"],
        session_id=request.session_id,
        message=request.message,
    )
    return await workflow.handle(
        public_workspace_id=config["workspace_public_id"],
        request=chat_request,
        idempotency_key=idempotency_key,
        http_response=http_response,
    )
