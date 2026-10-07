"""FastAPI routes for Oldy Buddy intelligence layer (text and voice conversation)."""

import base64
import logging
import re
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.core.contracts import Intent
from app.database import get_db
from app.models import ElderProfile, User, UserRole
from app.intelligence.conversation_service import (
    get_conversation_service,
    normalize_language_code,
    PLEASE_REPEAT_MESSAGES,
    DEFAULT_LANGUAGE,
)
from app.intelligence.exceptions import ProviderError
from app.intelligence.factory import get_providers
from app.intelligence.hooks import on_emergency_intent
from app.intelligence.schemas import ConverseRequest, ConverseResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/intelligence", tags=["intelligence"])

# Constants
MAX_AUDIO_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB
ALLOWED_AUDIO_TYPES = {
    "audio/wav",
    "audio/wave",
    "audio/x-wav",
    "audio/mpeg",
    "audio/mp3",
    "audio/ogg",
    "audio/webm",
    "audio/flac",
    "audio/m4a",
    "audio/aac",
    "application/octet-stream",
}


async def _resolve_elder_context(
    current_user: User,
    db: AsyncSession,
) -> tuple[int, dict[str, str], str]:
    """Authorize current user as ELDER and fetch elder profile language context."""
    if current_user.role != UserRole.ELDER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only elders may access conversation endpoints",
        )

    elder_id = current_user.id

    # Fetch elder profile for preferred language if available
    res = await db.execute(select(ElderProfile).where(ElderProfile.user_id == elder_id))
    profile = res.scalar_one_or_none()

    preferences = profile.preferences if profile and isinstance(profile.preferences, dict) else {}
    raw_lang = preferences.get("preferred_language") or preferences.get("language")
    language = normalize_language_code(raw_lang)

    profile_context = {
        "preferred_language": language,
        "preferences": preferences,
    }

    return elder_id, profile_context, language


@router.post("/converse", response_model=ConverseResponse)
async def converse_text(
    req: ConverseRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ConverseResponse:
    """Process a text-based conversation turn for an authenticated elder."""
    elder_id, profile_context, language = await _resolve_elder_context(current_user, db)

    conversation_service = get_conversation_service()
    providers = get_providers()

    # Process conversation turn
    converse_res = await conversation_service.process_turn(
        elder_id=elder_id,
        session_id=req.session_id,
        user_text=req.text,
        profile_context=profile_context,
    )

    # Call emergency hook if final intent is SOS or HELP
    if converse_res.intent in (Intent.SOS, Intent.HELP):
        await on_emergency_intent(
            elder_id=elder_id,
            intent=converse_res.intent,
            session_id=req.session_id,
            keyword_triggered=converse_res.emergency_keyword_triggered,
        )

    # Optional speech synthesis
    reply_audio_b64: Optional[str] = None
    if req.synthesize_voice:
        try:
            audio_bytes = await providers.tts.synthesize(converse_res.reply, language=language)
            reply_audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
        except Exception:
            # TTS failure still returns the text reply with reply_audio_base64 = None
            reply_audio_b64 = None

    # Privacy: Log only non-sensitive metadata at debug level (never user text or replies)
    logger.debug(
        "Text turn processed: elder_id=%s, session_id=%s, channel=%s, intent=%s",
        elder_id,
        req.session_id,
        req.channel,
        converse_res.intent.value,
    )

    return ConverseResponse(
        intent=converse_res.intent.value,
        reply_text=converse_res.reply,
        reply_audio_base64=reply_audio_b64,
        confidence=converse_res.confidence,
        session_id=req.session_id,
        language=language,
        is_safe=converse_res.is_safe,
        emergency_keyword_triggered=converse_res.emergency_keyword_triggered,
        user_transcript=None,
    )


@router.post("/converse-audio", response_model=ConverseResponse)
async def converse_audio(
    audio: UploadFile = File(..., description="Audio file to transcribe and process."),
    session_id: str = Form(..., description="Session identifier [A-Za-z0-9_-]."),
    channel: str = Form("app", description="Channel ('app' or 'call')."),
    synthesize_voice: bool = Form(True, description="Whether to synthesize reply audio."),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ConverseResponse:
    """Process an audio-based conversation turn (STT -> LLM -> TTS)."""
    # 1. Validate session_id
    clean_session = session_id.strip() if session_id else ""
    if not clean_session or len(clean_session) > 64 or not re.match(r"^[A-Za-z0-9_-]+$", clean_session):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="session_id must be 1-64 characters containing only [A-Za-z0-9_-]",
        )

    # 2. Validate channel
    if channel not in ("app", "call"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="channel must be either 'app' or 'call'",
        )

    # 3. Validate audio Content-Type
    if audio.content_type and audio.content_type.lower() not in ALLOWED_AUDIO_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported audio media type '{audio.content_type}'",
        )

    # 4. Read audio bytes with strict 10MB (+ 1 byte check) streaming limit
    audio_bytes = await audio.read(MAX_AUDIO_SIZE_BYTES + 1)
    if len(audio_bytes) > MAX_AUDIO_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Audio file exceeds 10MB size limit",
        )
    if len(audio_bytes) == 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Audio file cannot be empty",
        )

    # 5. Authorize elder and resolve language context
    elder_id, profile_context, language = await _resolve_elder_context(current_user, db)

    conversation_service = get_conversation_service()
    providers = get_providers()

    # 6. Transcribe audio via STT
    try:
        user_transcript = await providers.stt.transcribe(audio_bytes, language=language)
    except ProviderError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Voice service is currently unavailable. Please try again later.",
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Voice service is currently unavailable. Please try again later.",
        )

    clean_transcript = user_transcript.strip() if user_transcript else ""

    # 7. Handle empty transcript (polite repeat)
    if not clean_transcript:
        repeat_reply = PLEASE_REPEAT_MESSAGES.get(language, PLEASE_REPEAT_MESSAGES[DEFAULT_LANGUAGE])
        reply_audio_b64 = None
        if synthesize_voice:
            try:
                out_audio = await providers.tts.synthesize(repeat_reply, language=language)
                reply_audio_b64 = base64.b64encode(out_audio).decode("utf-8")
            except Exception:
                reply_audio_b64 = None

        return ConverseResponse(
            intent=Intent.UNKNOWN.value,
            reply_text=repeat_reply,
            reply_audio_base64=reply_audio_b64,
            confidence=0.0,
            session_id=clean_session,
            language=language,
            is_safe=True,
            emergency_keyword_triggered=False,
            user_transcript="",
        )

    # 8. Process turn through ConversationService
    converse_res = await conversation_service.process_turn(
        elder_id=elder_id,
        session_id=clean_session,
        user_text=clean_transcript,
        profile_context=profile_context,
    )

    # 9. Call emergency hook if final intent is SOS or HELP
    if converse_res.intent in (Intent.SOS, Intent.HELP):
        await on_emergency_intent(
            elder_id=elder_id,
            intent=converse_res.intent,
            session_id=clean_session,
            keyword_triggered=converse_res.emergency_keyword_triggered,
        )

    # 10. Synthesize voice if requested
    reply_audio_b64 = None
    if synthesize_voice:
        try:
            out_audio = await providers.tts.synthesize(converse_res.reply, language=language)
            reply_audio_b64 = base64.b64encode(out_audio).decode("utf-8")
        except Exception:
            reply_audio_b64 = None

    # Privacy: Log only non-sensitive metadata at debug level
    logger.debug(
        "Audio turn processed: elder_id=%s, session_id=%s, channel=%s, intent=%s",
        elder_id,
        clean_session,
        channel,
        converse_res.intent.value,
    )

    return ConverseResponse(
        intent=converse_res.intent.value,
        reply_text=converse_res.reply,
        reply_audio_base64=reply_audio_b64,
        confidence=converse_res.confidence,
        session_id=clean_session,
        language=language,
        is_safe=converse_res.is_safe,
        emergency_keyword_triggered=converse_res.emergency_keyword_triggered,
        user_transcript=clean_transcript,
    )
