from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class ChatRequest(BaseModel):
    customer_id: str | None = None
    visitor_id: str | None = None
    session_id: str = Field(min_length=1, max_length=255)
    identity_token: str | None = None
    message: str = Field(min_length=1, max_length=10_000)

    @field_validator("session_id")
    @classmethod
    def session_id_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("session_id cannot be blank")
        return value

    @model_validator(mode="after")
    def select_exactly_one_identity_type(self) -> "ChatRequest":
        if (self.customer_id is None) == (self.visitor_id is None):
            raise ValueError("Exactly one of customer_id or visitor_id is required")
        return self


class ChatResponse(BaseModel):
    response: str
    session_id: str
    sentiment: Literal["positive", "neutral", "negative", "frustrated", "unknown"] = "unknown"
    memories_used: list[str] = Field(default_factory=list)
    memory_retrieved: bool = False
    escalation_required: bool = False
    escalation_reason: str | None = None
