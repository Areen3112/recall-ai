from fastapi import APIRouter, HTTPException, Header, Request, Response
from uuid import UUID

from app.schemas.chat import ChatRequest, ChatResponse

router = APIRouter(prefix="/api/v1", tags=["Chat"])


@router.post("/chat")
async def chat(
    request_context: Request,
    http_response: Response,
    request: ChatRequest,
    x_workspace_id: str = Header(..., alias="X-Workspace-ID"),
    idempotency_key: str = Header(..., alias="Idempotency-Key", min_length=16, max_length=128),
) -> ChatResponse:
    try:
        UUID(x_workspace_id)
    except (ValueError, AttributeError) as exc:
        raise HTTPException(status_code=400, detail="Invalid workspace identifier") from exc
    workflow = getattr(request_context.app.state, "chat_workflow", None)
    if workflow is None:
        raise HTTPException(status_code=503, detail="Chat service is temporarily unavailable")
    return await workflow.handle(
        public_workspace_id=x_workspace_id,
        request=request,
        idempotency_key=idempotency_key,
        http_response=http_response,
    )
