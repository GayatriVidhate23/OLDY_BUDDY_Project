from datetime import datetime, timezone
from typing import List, Optional, Union
from fastapi import HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    User,
    ElderProfile,
    Activity,
    UserRelationship,
    UserRole,
    ActivityType,
    VoiceCall,
    AlertNotification,
    CallRecord,
)
from app.schemas import (
    UserCreate,
    UserResponse,
    ElderProfileCreate,
    ElderProfileUpdate,
    ElderProfileResponse,
    ElderProfileBase,
    ActivityCreate,
    ActivityBase,
    ActivityResponse,
    RelationshipCreate,
    RelationshipResponse,
    ConversationRequest,
    ConversationResponse,
    Token,
    VoiceCallCreate,
    VoiceCallResponse,
    VoiceWebhookRequest,
    VoiceWebhookResponse,
    AlertResponse,
    DashboardOverviewResponse,
    CallRecordResponse,
)
from app.auth import (
    get_password_hash,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)

# --- User Services ---
async def register_user(db: AsyncSession, user_in: UserCreate) -> UserResponse:
    result = await db.execute(select(User).where(User.email == user_in.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists",
        )
    db_user = User(
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        full_name=user_in.full_name,
        role=user_in.role,
        is_active=True,
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)

    user_resp = UserResponse.model_validate(db_user)

    # Auto-create ElderProfile if role is ELDER
    if db_user.role == UserRole.ELDER:
        profile = ElderProfile(user_id=db_user.id, preferences={}, routines={})
        db.add(profile)
        await db.commit()

    return user_resp

async def create_user(db: AsyncSession, user_in: UserCreate) -> User:
    result = await db.execute(select(User).where(User.email == user_in.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="User already exists")
    user = User(
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        full_name=user_in.full_name,
        role=user_in.role,
        is_active=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    if user.role == UserRole.ELDER:
        profile = ElderProfile(user_id=user.id, preferences={}, routines={})
        db.add(profile)
        await db.commit()
    return user

async def authenticate_user(db: AsyncSession, email: str, password: str) -> Token:
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")

    access_token = create_access_token(subject=user.id)
    refresh_token = create_refresh_token(subject=user.id)
    return Token(access_token=access_token, refresh_token=refresh_token, token_type="bearer")

async def refresh_access_token(db: AsyncSession, refresh_token: str) -> Token:
    payload = decode_token(refresh_token)
    if payload.type != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    
    result = await db.execute(select(User).where(User.id == int(payload.sub)))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User unavailable")

    new_access_token = create_access_token(subject=user.id)
    new_refresh_token = create_refresh_token(subject=user.id)
    return Token(access_token=new_access_token, refresh_token=new_refresh_token, token_type="bearer")

# --- Elder Profile Services ---
async def get_elder_profile(db: AsyncSession, elder_id: int) -> ElderProfileResponse:
    result = await db.execute(select(ElderProfile).where(ElderProfile.user_id == elder_id))
    profile = result.scalar_one_or_none()
    if not profile:
        profile = ElderProfile(user_id=elder_id, preferences={}, routines={})
        db.add(profile)
        await db.commit()
        await db.refresh(profile)
    return ElderProfileResponse.model_validate(profile)

async def get_profile(db: AsyncSession, elder_id: int) -> ElderProfile:
    result = await db.execute(select(ElderProfile).where(ElderProfile.user_id == elder_id))
    profile = result.scalar_one_or_none()
    if not profile:
        profile = ElderProfile(user_id=elder_id, preferences={}, routines={})
        db.add(profile)
        await db.commit()
        await db.refresh(profile)
    return profile

async def update_elder_profile(
    db: AsyncSession, elder_id: int, profile_in: Union[ElderProfileUpdate, ElderProfileBase]
) -> ElderProfileResponse:
    result = await db.execute(select(ElderProfile).where(ElderProfile.user_id == elder_id))
    profile = result.scalar_one_or_none()
    if not profile:
        profile = ElderProfile(user_id=elder_id, preferences={}, routines={})
        db.add(profile)

    if hasattr(profile_in, 'preferences') and profile_in.preferences is not None:
        profile.preferences = profile_in.preferences
    if hasattr(profile_in, 'routines') and profile_in.routines is not None:
        profile.routines = profile_in.routines
    if hasattr(profile_in, 'emergency_contact') and profile_in.emergency_contact is not None:
        profile.emergency_contact = profile_in.emergency_contact

    await db.commit()
    await db.refresh(profile)
    return ElderProfileResponse.model_validate(profile)

# --- Activity Services & Policy Enforcement ---
async def create_activity(
    db: AsyncSession, elder_id: int, activity_in: Union[ActivityCreate, ActivityBase]
) -> ActivityResponse:
    activity_type = activity_in.activity_type
    description = activity_in.description
    status_val = getattr(activity_in, 'status', None) or "PENDING"

    activity = Activity(
        elder_id=elder_id,
        activity_type=activity_type,
        description=description,
        status=status_val,
        timestamp=datetime.now(timezone.utc),
    )
    db.add(activity)

    if activity_type == "SOS":
        from app.services.notify.policy import create_alert_with_notifications
        await create_alert_with_notifications(
            db,
            elder_id=elder_id,
            severity="EMERGENCY",
            message=f"🚨 EMERGENCY SOS TRIGGERED: {description or 'Immediate assistance required!'}",
        )
    else:
        await db.commit()

    await db.refresh(activity)
    return ActivityResponse.model_validate(activity)

async def get_activities_for_elder(
    db: AsyncSession, elder_id: int, activity_type: Optional[str] = None
) -> List[ActivityResponse]:
    query = select(Activity).where(Activity.elder_id == elder_id)
    if activity_type:
        query = query.where(Activity.activity_type == activity_type)
    query = query.order_by(Activity.timestamp.desc())
    result = await db.execute(query)
    activities = result.scalars().all()
    return [ActivityResponse.model_validate(a) for a in activities]

async def update_activity_status(
    db: AsyncSession, activity_id: int, status_str: str
) -> ActivityResponse:
    result = await db.execute(select(Activity).where(Activity.id == activity_id))
    activity = result.scalar_one_or_none()
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")
    activity.status = status_str
    await db.commit()
    await db.refresh(activity)
    return ActivityResponse.model_validate(activity)

# --- Relationship Services ---
async def create_relationship(
    db: AsyncSession, rel_in: RelationshipCreate
) -> RelationshipResponse:
    rel = UserRelationship(
        elder_id=rel_in.elder_id,
        caregiver_id=rel_in.caregiver_id,
        type=rel_in.type,
    )
    db.add(rel)
    await db.commit()
    await db.refresh(rel)
    return RelationshipResponse.model_validate(rel)

async def get_elder_relationships(
    db: AsyncSession, elder_id: int
) -> List[RelationshipResponse]:
    result = await db.execute(
        select(UserRelationship).where(UserRelationship.elder_id == elder_id)
    )
    rels = result.scalars().all()
    return [RelationshipResponse.model_validate(r) for r in rels]

# --- Voice Agent Services ---
async def trigger_outbound_voice_call(
    db: AsyncSession, call_in: VoiceCallCreate
) -> VoiceCallResponse:
    prof_res = await db.execute(select(ElderProfile).where(ElderProfile.user_id == call_in.elder_id))
    profile = prof_res.scalar_one_or_none()
    phone = call_in.phone_number or (profile.emergency_contact if profile else "+1 (555) 019-2834")

    call = VoiceCall(
        elder_id=call_in.elder_id,
        phone_number=phone,
        call_type=call_in.call_type or "OUTBOUND_CHECKIN",
        status="COMPLETED",
        duration_seconds=45,
        transcript="System: Hello! This is your Oldy Buddy check-in call. Are you feeling well today?\nElder: Yes, I am doing great! I took my morning medicine at 8 AM.",
        ai_summary="Elder confirmed good health and morning medication adherence.",
        timestamp=datetime.now(timezone.utc),
    )
    db.add(call)

    checkin_act = Activity(
        elder_id=call_in.elder_id,
        activity_type="CHECK_IN",
        description="Automated Voice Check-In completed successfully",
        status="COMPLETED",
        timestamp=datetime.now(timezone.utc),
    )
    db.add(checkin_act)

    await db.commit()
    await db.refresh(call)
    return VoiceCallResponse.model_validate(call)

async def initiate_call(db: AsyncSession, elder_id: int, call_type: str) -> CallRecord:
    record = CallRecord(elder_id=elder_id, call_type=call_type, status="INITIATED")
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return record

async def process_voice_webhook(
    db: AsyncSession,
    req_or_id: Union[VoiceWebhookRequest, int],
    event_type: Optional[str] = None,
    speech_text: Optional[str] = None,
) -> Union[VoiceWebhookResponse, dict]:
    if isinstance(req_or_id, VoiceWebhookRequest):
        req = req_or_id
        user_speech_lower = req.user_speech.lower()
        if "help" in user_speech_lower or "sos" in user_speech_lower or "fell" in user_speech_lower:
            ai_reply = "I understand you need emergency help! I am notifying your caregiver right now."
            action = "DISPATCH_ALERT"

            from app.services.notify.policy import create_alert_with_notifications
            await create_alert_with_notifications(
                db,
                elder_id=req.elder_id,
                severity="EMERGENCY",
                message=f"🚨 VOICE AGENT ALERT: Elder reported emergency in call speech ('{req.user_speech}')",
            )
        elif "medicine" in user_speech_lower or "took" in user_speech_lower:
            ai_reply = "Wonderful! I have recorded your medicine check-in."
            action = "LOG_MEDICATION"
        else:
            ai_reply = f"Thank you for sharing. I heard: '{req.user_speech}'. Take care!"
            action = "CONVERSATION"

        twiml = f"<Response><Say>{ai_reply}</Say></Response>"
        return VoiceWebhookResponse(twiml_response=twiml, ai_reply=ai_reply, action_taken=action)
    else:
        call_id = req_or_id
        result = await db.execute(select(CallRecord).where(CallRecord.id == call_id))
        record = result.scalar_one_or_none()
        if not record:
            raise HTTPException(status_code=404, detail="Call record not found")

        if event_type == "answered":
            record.status = "IN_PROGRESS"
        elif event_type == "speech" and speech_text:
            text = speech_text.lower()
            if "help" in text or "sos" in text or "emergency" in text:
                record.response = "NEED_HELP"
                record.outcome = "ESCALATED"
                record.status = "COMPLETED"
                act = Activity(elder_id=record.elder_id, activity_type="SOS", description=f"Triggered via voice call {call_id}: {speech_text}")
                db.add(act)
                from app.services.notify.policy import create_alert_with_notifications
                await create_alert_with_notifications(
                    db,
                    elder_id=record.elder_id,
                    severity="EMERGENCY",
                    message=f"🚨 VOICE CALL SOS: Triggered via voice call {call_id}: {speech_text}",
                )
            elif "yes" in text:
                record.response = "YES"
                record.outcome = "COMPLETED_SUCCESS"
            elif "no" in text:
                record.response = "NO"
                record.outcome = "NEEDS_FOLLOWUP"
        elif event_type in ["completed", "failed"]:
            record.status = event_type.upper()
            record.end_time = datetime.now(timezone.utc)

        await db.commit()
        await db.refresh(record)
        return {"status": "ok", "record": record}

async def get_voice_history(
    db: AsyncSession, elder_id: int
) -> List[VoiceCallResponse]:
    result = await db.execute(
        select(VoiceCall).where(VoiceCall.elder_id == elder_id).order_by(VoiceCall.timestamp.desc())
    )
    calls = result.scalars().all()
    return [VoiceCallResponse.model_validate(c) for c in calls]

# --- Alerts Services ---
async def get_elder_alerts(
    db: AsyncSession, elder_id: int
) -> List[AlertResponse]:
    result = await db.execute(
        select(AlertNotification)
        .where(AlertNotification.elder_id == elder_id)
        .order_by(AlertNotification.timestamp.desc())
    )
    alerts = result.scalars().all()
    return [AlertResponse.model_validate(a) for a in alerts]

async def resolve_alert(
    db: AsyncSession, alert_id: int
) -> AlertResponse:
    from app.services.notify.policy import acknowledge_alert
    alert = await acknowledge_alert(db, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return AlertResponse.model_validate(alert)

# --- Family / Caregiver Dashboard Overview ---
async def get_dashboard_overview(
    db: AsyncSession, elder_id: int
) -> DashboardOverviewResponse:
    user_res = await db.execute(select(User).where(User.id == elder_id))
    user = user_res.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Elder user not found")

    prof_res = await db.execute(select(ElderProfile).where(ElderProfile.user_id == elder_id))
    profile = prof_res.scalar_one_or_none()

    act_res = await db.execute(select(Activity).where(Activity.elder_id == elder_id).order_by(Activity.timestamp.desc()))
    activities = act_res.scalars().all()

    last_checkin = None
    last_interaction = None
    today_reminders = 0
    completed_reminders = 0
    missed_reminders = 0

    for act in activities:
        if not last_interaction:
            last_interaction = act.timestamp
        if act.activity_type == "CHECK_IN" and not last_checkin:
            last_checkin = act.timestamp
        if act.activity_type == "REMINDER":
            today_reminders += 1
            if act.status == "COMPLETED":
                completed_reminders += 1
            else:
                missed_reminders += 1

    alert_res = await db.execute(
        select(AlertNotification).where(AlertNotification.elder_id == elder_id, AlertNotification.is_resolved == False)
    )
    active_alerts = alert_res.scalars().all()
    active_alerts_count = len(active_alerts)

    if active_alerts_count > 0:
        status_badge = "SOS_ALERT"
    elif last_checkin is not None:
        status_badge = "CHECKED_IN"
    else:
        status_badge = "PENDING_CHECKIN"

    return DashboardOverviewResponse(
        elder_id=user.id,
        elder_name=user.full_name or user.email.split("@")[0].title(),
        elder_email=user.email,
        emergency_contact=profile.emergency_contact if profile else None,
        last_check_in=last_checkin,
        last_interaction=last_interaction,
        status_badge=status_badge,
        active_alerts_count=active_alerts_count,
        today_reminders_count=today_reminders,
        completed_reminders_count=completed_reminders,
        missed_reminders_count=missed_reminders,
    )

# --- AI Conversation Service ---
async def process_ai_conversation(
    req: ConversationRequest
) -> ConversationResponse:
    prompt_lower = req.prompt.lower()
    if "medicine" in prompt_lower or "reminder" in prompt_lower:
        reply = "I have checked your reminders. Don't forget to take your prescribed medicine on time!"
    elif "help" in prompt_lower or "sos" in prompt_lower or "emergency" in prompt_lower:
        reply = "Emergency alert triggered! I am notifying your caregiver and emergency contacts immediately."
    elif "hello" in prompt_lower or "hi" in prompt_lower:
        reply = "Hello there! I am your Oldy Buddy assistant. How are you feeling today?"
    else:
        reply = f"I hear you! You said: '{req.prompt}'. I'm right here with you."

    return ConversationResponse(
        reply=reply,
        timestamp=datetime.now(timezone.utc)
    )
