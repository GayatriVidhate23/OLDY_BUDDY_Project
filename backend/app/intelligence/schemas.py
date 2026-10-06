"""Pydantic schemas for the intelligence layer."""

from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

from app.core.contracts import Intent


class IntentClassificationResult(BaseModel):
    """Structured result of intent classification and conversational reply."""

    model_config = ConfigDict(extra="ignore")

    intent: Intent = Field(..., description="Classified intent from the conversation.")
    reply: str = Field(..., description="Safe, warm conversational reply for the elder.")
    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Confidence score between 0.0 and 1.0.",
    )
    reasoning: Optional[str] = Field(
        default=None,
        description="Optional brief explanation of why this intent was selected.",
    )


class GuardrailResult(BaseModel):
    """Result of applying safety guardrails to an AI conversational reply."""

    model_config = ConfigDict(extra="ignore")

    is_safe: bool = Field(..., description="Whether the original reply passed all safety checks without alteration.")
    sanitized_reply: str = Field(..., description="Safe, sanitized conversational reply text.")
    violations: list[str] = Field(default_factory=list, description="List of detected safety violation categories.")
    fallback_triggered: bool = Field(default=False, description="Whether a safety fallback replaced the original reply.")
