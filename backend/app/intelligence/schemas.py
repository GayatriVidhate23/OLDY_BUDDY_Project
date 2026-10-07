"""Pydantic schemas for the intelligence layer."""

import re
from typing import Literal, Optional
from pydantic import BaseModel, Field, ConfigDict, field_validator

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


class ConverseResult(BaseModel):
    """Structured result of processing a conversation turn in ConversationService."""

    model_config = ConfigDict(extra="ignore")

    elder_id: int = Field(..., description="ID of the elder user.")
    session_id: str = Field(..., description="Unique ID for the conversation session.")
    intent: Intent = Field(..., description="Final classified Intent.")
    reply: str = Field(..., description="Sanitized conversational reply text.")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score.")
    is_safe: bool = Field(..., description="Whether reply passed all safety guardrails.")
    violations: list[str] = Field(default_factory=list, description="Safety violation categories if any.")
    language: str = Field(..., description="Normalized language code (e.g., 'en-IN', 'hi-IN', 'mr-IN').")
    emergency_keyword_triggered: bool = Field(
        default=False,
        description="Whether a deterministic emergency keyword triggered an intent upgrade.",
    )


class ConverseRequest(BaseModel):
    """Request payload for text-based conversation route."""

    model_config = ConfigDict(extra="ignore")

    text: str = Field(..., description="User message text (1-1000 characters).")
    session_id: str = Field(..., max_length=64, description="Unique session ID [A-Za-z0-9_-].")
    channel: Literal["app", "call"] = Field(default="app", description="Communication channel.")
    synthesize_voice: bool = Field(default=False, description="Whether to synthesize speech audio.")

    @field_validator("text")
    @classmethod
    def validate_text(cls, v: str) -> str:
        stripped = v.strip() if v else ""
        if not stripped:
            raise ValueError("Text cannot be empty or whitespace only.")
        if len(stripped) > 1000:
            raise ValueError("Text cannot exceed 1000 characters.")
        return stripped

    @field_validator("session_id")
    @classmethod
    def validate_session_id(cls, v: str) -> str:
        stripped = v.strip() if v else ""
        if not stripped:
            raise ValueError("session_id cannot be empty.")
        if len(stripped) > 64:
            raise ValueError("session_id cannot exceed 64 characters.")
        if not re.match(r"^[A-Za-z0-9_-]+$", stripped):
            raise ValueError("session_id must contain only alphanumeric characters, underscores, or hyphens.")
        return stripped


class ConverseResponse(BaseModel):
    """Structured response for conversation endpoints."""

    model_config = ConfigDict(extra="ignore")

    intent: str = Field(..., description="Classified intent value.")
    reply_text: str = Field(..., description="Sanitized conversational reply text.")
    reply_audio_base64: Optional[str] = Field(
        default=None,
        description="Base64-encoded synthesized audio if requested, else None.",
    )
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score.")
    session_id: str = Field(..., description="Conversation session ID.")
    language: str = Field(..., description="Normalized language code.")
    is_safe: bool = Field(default=True, description="Whether reply passed all safety guardrails.")
    emergency_keyword_triggered: bool = Field(
        default=False,
        description="Whether a deterministic keyword triggered an intent upgrade.",
    )
    user_transcript: Optional[str] = Field(
        default=None,
        description="User speech transcript if audio was provided.",
    )
