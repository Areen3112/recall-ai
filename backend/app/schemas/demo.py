from pydantic import BaseModel, ConfigDict, Field, field_validator


class DashboardDemoChatRequest(BaseModel):
    """Browser input accepted by the development-only Sarah dashboard demo."""

    model_config = ConfigDict(extra="forbid")

    session_id: str = Field(min_length=1, max_length=255)
    message: str = Field(min_length=1, max_length=10_000)

    @field_validator("session_id", "message")
    @classmethod
    def value_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Value cannot be blank")
        return value
