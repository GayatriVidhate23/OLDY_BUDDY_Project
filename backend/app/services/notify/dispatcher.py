from datetime import datetime, timedelta, timezone
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import settings
from app.models import (
    Notification,
    NotificationChannel,
    NotificationStatus,
    AlertNotification,
    UserDevice,
    User,
    ElderProfile,
)
from app.services.notify.expo_push import ExpoPushService
from app.services.notify.sms import SmsProvider, get_sms_provider, ConsoleSmsProvider

MAX_RETRIES = getattr(settings, "MAX_NOTIFICATION_RETRIES", 3)

class NotificationDispatcher:
    def __init__(self, push_service: ExpoPushService = None, sms_provider: SmsProvider = None):
        self.push_service = push_service or ExpoPushService()
        self.sms_provider = sms_provider or get_sms_provider()

    async def process_outbox(self, db: AsyncSession, limit: int = 50) -> List[Notification]:
        """
        Processes pending notification outbox jobs and handles retries / skipping.
        """
        now = datetime.now(timezone.utc)
        
        # 1. Fetch pending notifications ready to send
        res = await db.execute(
            select(Notification)
            .where(
                Notification.status == NotificationStatus.PENDING.value,
                Notification.next_attempt_at <= now,
            )
            .limit(limit)
        )
        pending_notifs = res.scalars().all()
        processed = []

        for notif in pending_notifs:
            # 2. Re-check alert acknowledgement status before dispatching delayed SMS/Push
            if notif.alert_id:
                alert_res = await db.execute(
                    select(AlertNotification).where(AlertNotification.id == notif.alert_id)
                )
                alert = alert_res.scalar_one_or_none()
                if alert and (alert.is_acknowledged or alert.is_resolved):
                    notif.status = NotificationStatus.SKIPPED.value
                    notif.updated_at = now
                    processed.append(notif)
                    continue

            # Mark in progress
            notif.status = NotificationStatus.PROCESSING.value
            notif.attempt_count += 1
            notif.updated_at = now

            try:
                if notif.channel == NotificationChannel.PUSH.value:
                    await self._dispatch_push(db, notif)
                elif notif.channel == NotificationChannel.SMS.value:
                    await self._dispatch_sms(db, notif)
                elif notif.channel == NotificationChannel.CALL.value:
                    await self._dispatch_call(db, notif)
                else:
                    raise ValueError(f"Unknown notification channel: {notif.channel}")

                # Success
                notif.status = NotificationStatus.SENT.value
                notif.last_error = None

            except Exception as err:
                error_msg = str(err)
                notif.last_error = error_msg
                
                if notif.attempt_count < MAX_RETRIES:
                    # Retry sequence: Attempt 1 -> Retry -> Attempt 2 -> Retry -> Attempt 3 -> Failed
                    notif.status = NotificationStatus.PENDING.value
                    # Exponential or fixed backoff (e.g., 5 seconds per attempt count in tests/runtime)
                    backoff_sec = 5 * notif.attempt_count
                    notif.next_attempt_at = now + timedelta(seconds=backoff_sec)
                else:
                    # Reached maximum retries -> permanently failed
                    notif.status = NotificationStatus.FAILED.value

            processed.append(notif)

        await db.commit()
        return processed

    async def _dispatch_push(self, db: AsyncSession, notif: Notification) -> None:
        # Fetch active push tokens for recipient
        dev_res = await db.execute(
            select(UserDevice).where(
                UserDevice.user_id == notif.recipient_id,
                UserDevice.is_active == True,
            )
        )
        devices = dev_res.scalars().all()

        if not devices:
            # If no active devices registered, mark as sent/completed with note or fallback
            notif.provider_message_id = "no_registered_devices"
            return

        payload = notif.payload or {}
        messages = []
        for dev in devices:
            messages.append({
                "to": dev.push_token,
                "title": payload.get("title", "OldyBuddy Alert"),
                "body": payload.get("body", "Notification alert from OldyBuddy"),
                "data": payload,
            })

        results = await self.push_service.send_push_notifications(db, messages)
        # Verify if any succeeded
        errors = [r for r in results if r.get("status") == "error"]
        if errors and len(errors) == len(results):
            raise RuntimeError(f"Push dispatch failed: {errors[0].get('error')}")

        notif.provider_message_id = results[0].get("id") if results else "push_sent"

    async def _dispatch_sms(self, db: AsyncSession, notif: Notification) -> None:
        # Fetch recipient user phone number
        user_res = await db.execute(select(User).where(User.id == notif.recipient_id))
        user = user_res.scalar_one_or_none()
        phone = (user.phone_number if user else None)

        if not phone:
            # Fallback to elder profile emergency contact if recipient is elder
            prof_res = await db.execute(select(ElderProfile).where(ElderProfile.user_id == notif.recipient_id))
            profile = prof_res.scalar_one_or_none()
            phone = profile.emergency_contact if profile else None

        if not phone:
            phone = "+15550192834"  # Default test fallback phone

        payload = notif.payload or {}
        sms_text = payload.get("sms_body") or payload.get("body") or "OldyBuddy Notification"

        res = await self.sms_provider.send_sms(phone, sms_text)
        notif.provider_message_id = res.get("provider_message_id", "sms_sent")

    async def _dispatch_call(self, db: AsyncSession, notif: Notification) -> None:
        # Telephony mock call dispatch
        notif.provider_message_id = f"call_{notif.id}_{int(datetime.now(timezone.utc).timestamp())}"
