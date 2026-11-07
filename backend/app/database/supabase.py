from supabase import AsyncClient, create_async_client

from app.core.config import Settings


async def create_supabase_client(settings: Settings) -> AsyncClient | None:
    """Create an async service client; never use the browser's publishable key here."""
    if not settings.supabase_url or not settings.supabase_service_role_key:
        return None
    return await create_async_client(
        str(settings.supabase_url),
        settings.supabase_service_role_key.get_secret_value(),
    )


async def close_supabase_client(client: AsyncClient | None) -> None:
    if client is None:
        return
    try:
        await client.postgrest.aclose()
    finally:
        await client.auth.close()
