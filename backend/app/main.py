from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import chat, demo, health
from app.agents.support_agent import SupportAgent, SupportAgentError
from app.core.config import get_settings
from app.database.chat_repository import ChatRepository
from app.database.chat_repository import ChatRepositoryError
from app.database.supabase import close_supabase_client, create_supabase_client
from app.services.chat_workflow import ChatWorkflow
from app.memory.hindsight_client import create_hindsight_client
from app.memory.memory_service import MemoryService, MemoryServiceError


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    app.state.settings = settings
    supabase = None
    hindsight = None
    support_agent = None
    try:
        supabase = await create_supabase_client(settings)
        app.state.supabase = supabase
        hindsight = create_hindsight_client(settings)
        app.state.hindsight = hindsight
        memory_service = None
        if hindsight is not None and settings.hindsight_bank_id_secret is not None:
            memory_service = MemoryService(hindsight, bank_id_secret=settings.hindsight_bank_id_secret)
        repository = ChatRepository(supabase) if supabase is not None else None
        if repository is not None and memory_service is not None and settings.groq_api_key is not None:
            support_agent = SupportAgent(settings=settings, memory_service=memory_service)
        app.state.support_agent = support_agent
        app.state.chat_workflow = (
            ChatWorkflow(
                repository=repository,
                memory_service=memory_service,
                support_agent=support_agent,
                settings=settings,
            )
            if repository is not None and memory_service is not None and support_agent is not None
            else None
        )
        yield
    finally:
        try:
            if support_agent is not None:
                await support_agent.aclose()
        finally:
            try:
                if hindsight is not None:
                    await hindsight.aclose()
            finally:
                await close_supabase_client(supabase)


def create_app() -> FastAPI:
    settings = get_settings()
    application = FastAPI(title="RECALL AI API", version="1.0.0", lifespan=lifespan)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Workspace-ID", "Idempotency-Key"],
        expose_headers=["X-Workflow-Status", "X-Memory-Status"],
    )
    application.include_router(health.router)
    application.include_router(chat.router)
    application.include_router(demo.router)

    @application.exception_handler(MemoryServiceError)
    async def memory_service_error_handler(_, exc: MemoryServiceError) -> JSONResponse:
        return JSONResponse(status_code=503, content={"detail": exc.public_message})

    @application.exception_handler(SupportAgentError)
    async def support_agent_error_handler(_, exc: SupportAgentError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.public_message})

    @application.exception_handler(ChatRepositoryError)
    async def repository_error_handler(_, exc: ChatRepositoryError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.public_message})

    @application.exception_handler(RequestValidationError)
    async def request_validation_error_handler(_, __: RequestValidationError) -> JSONResponse:
        return JSONResponse(status_code=400, content={"detail": "Invalid request"})

    @application.exception_handler(Exception)
    async def unexpected_error_handler(_, __: Exception) -> JSONResponse:
        return JSONResponse(status_code=500, content={"detail": "Internal server error"})

    return application


app = create_app()
