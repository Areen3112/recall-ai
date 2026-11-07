from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class SupportAgentOutput(BaseModel):
    """Validated internal result. Suggested facts are never persisted by this schema."""

    model_config = ConfigDict(extra="forbid")

    response: str = Field(min_length=1)
    sentiment: Literal["positive", "neutral", "negative", "frustrated", "unknown"]
    memories_used: list[str]
    memory_retrieved: bool
    escalation_required: bool
    escalation_reason: str
    interaction_summary: str
    suggested_memory_facts: list[str] = Field(max_length=5)

    @field_validator("suggested_memory_facts")
    @classmethod
    def limit_suggestion_size(cls, value: list[str]) -> list[str]:
        if any(len(fact) > 500 for fact in value):
            raise ValueError("Suggested memory facts must be no longer than 500 characters")
        return value


SUPPORT_AGENT_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "response": {"type": "string"},
        "sentiment": {"type": "string", "enum": ["positive", "neutral", "negative", "frustrated", "unknown"]},
        "memories_used": {"type": "array", "items": {"type": "string"}},
        "memory_retrieved": {"type": "boolean"},
        "escalation_required": {"type": "boolean"},
        "escalation_reason": {"type": "string"},
        "interaction_summary": {"type": "string"},
        "suggested_memory_facts": {"type": "array", "maxItems": 5, "items": {"type": "string", "maxLength": 500}},
    },
    "required": [
        "response",
        "sentiment",
        "memories_used",
        "memory_retrieved",
        "escalation_required",
        "escalation_reason",
        "interaction_summary",
        "suggested_memory_facts",
    ],
    "additionalProperties": False,
}
