from hindsight_client import Hindsight

from app.core.config import Settings


def create_hindsight_client(settings: Settings) -> Hindsight | None:
    if not settings.hindsight_api_key:
        return None
    return Hindsight(
        base_url=str(settings.hindsight_base_url),
        api_key=settings.hindsight_api_key.get_secret_value(),
        timeout=20.0,
        max_attempts=1,
    )
