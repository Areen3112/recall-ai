from functools import lru_cache

from pydantic import AnyHttpUrl, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    allow_synthetic_demo_seed: bool = False
    secret_key: SecretStr = SecretStr("change-me")
    frontend_url: str = "http://localhost:5173"
    groq_api_key: SecretStr | None = None
    groq_model: str = "openai/gpt-oss-120b"
    groq_timeout_seconds: float = 30.0
    groq_context_budget_bytes: int = 8_192
    supabase_url: AnyHttpUrl | None = None
    supabase_service_role_key: SecretStr | None = None
    hindsight_api_key: SecretStr | None = None
    hindsight_bank_id_secret: SecretStr | None = None
    hindsight_base_url: AnyHttpUrl = "https://api.hindsight.vectorize.io"
    identity_token_secret: SecretStr | None = None
    identity_token_issuer: str | None = None
    identity_token_audience: str | None = None
    identity_token_max_ttl_seconds: int = 3600
    demo_supabase_project_ref: str | None = None
    demo_supabase_project_allowlist: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    @model_validator(mode="after")
    def require_production_signing_secrets(self) -> "Settings":
        if not 1.0 <= self.groq_timeout_seconds <= 60.0:
            raise ValueError("GROQ_TIMEOUT_SECONDS must be between 1 and 60 seconds")
        if not 8_192 <= self.groq_context_budget_bytes <= 2_000_000:
            raise ValueError("GROQ_CONTEXT_BUDGET_BYTES must be between 8192 and 2000000")
        if not 60 <= self.identity_token_max_ttl_seconds <= 86400:
            raise ValueError("IDENTITY_TOKEN_MAX_TTL_SECONDS must be between 60 and 86400")
        if (
            self.hindsight_bank_id_secret
            and self.identity_token_secret
            and self.hindsight_bank_id_secret.get_secret_value()
            == self.identity_token_secret.get_secret_value()
        ):
            raise ValueError("Hindsight bank ID and identity signing secrets must be different")
        if self.app_env.lower() in {"prod", "production"}:
            if not self.hindsight_bank_id_secret or len(
                self.hindsight_bank_id_secret.get_secret_value().encode("utf-8")
            ) < 32:
                raise ValueError("HINDSIGHT_BANK_ID_SECRET must be at least 32 bytes in production")
            if not self.identity_token_secret or len(
                self.identity_token_secret.get_secret_value().encode("utf-8")
            ) < 32:
                raise ValueError("IDENTITY_TOKEN_SECRET must be at least 32 bytes in production")
        return self

    @property
    def cors_origins(self) -> list[str]:
        return [self.frontend_url]


@lru_cache
def get_settings() -> Settings:
    return Settings()
