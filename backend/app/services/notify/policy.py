from datetime import datetime, timedelta, timezone
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    User,
    UserRole,
    UserRelationship,
    AlertNotification,
    Notification,
    NotificationChannel,
    NotificationStatus,
    ElderProfile,
)
from app.services.notify.templates import get_notification_template

async def get_elder_caregivers(db: AsyncSession, elder_id: int) -> List[User]:
    """
    Find all caregivers linked to the elder via UserRelationship or ADMINs.
    """
    rel_res = await db.execute(
        select(UserRelationship.caregiver_id).where(UserRelationship.elder_id == elder_id)
    )
    caregiver_ids = rel_res.scalars().all()

    if not caregiver_ids:
        # Fallback to any CAREGIVER or ADMIN role user in the system if no direct relationship defined
        user_res = await db.execute(
            select(User).where(User.role.in_([UserRole.CAREGIVER, UserRole.ADMIN]))
        )
        return user_res.scalars().all()

    user_res = await db.execute(select(User).where(User.id.in_(caregiver_ids)))
    return user_res.scalars().all()

async def create_alert_with_notifications(
    db: AsyncSession,
    elder_id: int,
    severity: str,
    message: str,
    title: Optional[str] = None,
    warning_delay_minutes: int = 15,
) -> AlertNotification:
    """
    Outbox Pattern:
    Create AlertNotification record and corresponding Notification outbox jobs in the SAME DB TRANSACTION.
    """
    now = datetime.now(timezone.utc)
    sev_upper = severity.upper()
    
    # Normalize severity string
    if sev_upper in ["HIGH", "CRITICAL"]:
        sev_upper = "EMERGENCY"
    elif sev_upper in ["MEDIUM"]:
        sev_upper = "WARNING"
    elif sev_upper in ["LOW"]:
        sev_upper = "INFO"

    # 1. Create AlertNotification record
    alert = AlertNotification(
        elder_id=elder_id,
        severity=sev_upper,
        message=message,
        is_resolved=False,
        is_acknowledged=False,
        escalation_stage=1,
        escalation_status="ACTIVE",
        timestamp=now,
    )
    db.add(alert)
    await db.flush()  # Ensures alert.id is generated within the active transaction

    # 2. Fetch Elder details
    elder_res = await db.execute(select(User).where(User.id == elder_id))
    elder_user = elder_res.scalar_one_or_none()
    elder_name = (elder_user.full_name or elder_user.email.split("@")[0].title()) if elder_user else f"Elder #{elder_id}"

    # Get notification message payload
    tmpl = get_notification_template(sev_upper, elder_name, message)
    payload = {
        "title": title or tmpl["title"],
        "body": tmpl["body"],
        "sms_body": tmpl["sms"],
        "severity": sev_upper,
        "elder_id": elder_id,
        "alert_id": alert.id,
    }

    caregivers = await get_elder_caregivers(db, elder_id)

    # 3. Notification Policy Logic
    if sev_upper == "INFO":
        # INFO: Push immediately to all caregivers
        for cg in caregivers:
            notif = Notification(
                alert_id=alert.id,
                recipient_id=cg.id,
                channel=NotificationChannel.PUSH.value,
                status=NotificationStatus.PENDING.value,
                attempt_count=0,
                next_attempt_at=now,
                payload=payload,
                created_at=now,
                updated_at=now,
            )
            db.add(notif)

    elif sev_upper == "WARNING":
        # WARNING: Push immediately -> all caregivers. Schedule SMS for +15 minutes
        sms_next_attempt = now + timedelta(minutes=warning_delay_minutes)

        for cg in caregivers:
            # Immediate Push Job
            push_notif = Notification(
                alert_id=alert.id,
                recipient_id=cg.id,
                channel=NotificationChannel.PUSH.value,
                status=NotificationStatus.PENDING.value,
                attempt_count=0,
                next_attempt_at=now,
                payload=payload,
                created_at=now,
                updated_at=now,
            )
            db.add(push_notif)

            # Scheduled SMS Job (+15 mins)
            sms_notif = Notification(
                alert_id=alert.id,
                recipient_id=cg.id,
                channel=NotificationChannel.SMS.value,
                status=NotificationStatus.PENDING.value,
                attempt_count=0,
                next_attempt_at=sms_next_attempt,
                payload=payload,
                created_at=now,
                updated_at=now,
            )
            db.add(sms_notif)

    elif sev_upper == "EMERGENCY":
        # EMERGENCY: Step 5.5 Escalation Ladder
        # Stage 1: Caregivers immediately via Push, SMS, and Call
        for cg in caregivers:
            for ch in [NotificationChannel.PUSH.value, NotificationChannel.SMS.value, NotificationChannel.CALL.value]:
                notif = Notification(
                    alert_id=alert.id,
                    recipient_id=cg.id,
                    channel=ch,
                    status=NotificationStatus.PENDING.value,
                    attempt_count=0,
                    next_attempt_at=now,
                    payload=payload,
                    created_at=now,
                    updated_at=now,
                )
                db.add(notif)

    # Both Alert and Notification Outbox records are committed together in the transaction
    await db.commit()
    await db.refresh(alert)
    return alert

async def acknowledge_alert(
    db: AsyncSession, alert_id: int, user_id: Optional[int] = None
) -> Optional[AlertNotification]:
    """
    Acknowledge an alert and skip any pending delayed notifications.
    """
    now = datetime.now(timezone.utc)
    res = await db.execute(select(AlertNotification).where(AlertNotification.id == alert_id))
    alert = res.scalar_one_or_none()
    if not alert:
        return None

    alert.is_acknowledged = True
    alert.is_resolved = True
    alert.acknowledged_at = now
    alert.acknowledged_by_id = user_id
    alert.escalation_status = "ACKNOWLEDGED"

    # Mark all pending delayed SMS/Call notifications for this alert as SKIPPED
    notif_res = await db.execute(
        select(Notification).where(
            Notification.alert_id == alert_id,
            Notification.status == NotificationStatus.PENDING.value,
        )
    )
    pending_notifs = notif_res.scalars().all()
    for n in pending_notifs:
        n.status = NotificationStatus.SKIPPED.value
        n.updated_at = now

    await db.commit()
    await db.refresh(alert)
    return alert

async def escalate_emergency_alert(db: AsyncSession, alert_id: int) -> bool:
    """
    Escalate an emergency alert to Stage 2 (Emergency Contacts) if unacknowledged.
    Escalation operates independently of individual SMS/Call job failures.
    """
    now = datetime.now(timezone.utc)
    res = await db.execute(select(AlertNotification).where(AlertNotification.id == alert_id))
    alert = res.scalar_one_or_none()
    if not alert or alert.is_acknowledged or alert.is_resolved:
        return False

    alert.escalation_stage += 1
    alert.escalation_status = "ESCALATED"

    # Get emergency contact for elder
    prof_res = await db.execute(select(ElderProfile).where(ElderProfile.user_id == alert.elder_id))
    profile = prof_res.scalar_one_or_none()

    # Get elder details
    elder_res = await db.execute(select(User).where(User.id == alert.elder_id))
    elder_user = elder_res.scalar_one_or_none()
    elder_name = (elder_user.full_name or elder_user.email.split("@")[0].title()) if elder_user else f"Elder #{alert.elder_id}"

    tmpl = get_notification_template("EMERGENCY", elder_name, alert.message)
    payload = {
        "title": f"🚨 ESCALATED EMERGENCY: {elder_name}",
        "body": f"ESCALATED STAGE {alert.escalation_stage}: {alert.message}",
        "sms_body": f"🚨 ESCALATED EMERGENCY for {elder_name}: {alert.message}. Please respond immediately!",
        "severity": "EMERGENCY",
        "elder_id": alert.elder_id,
        "alert_id": alert.id,
        "escalation_stage": alert.escalation_stage,
    }

    # Dispatch to emergency contact or all caregivers/family
    caregivers = await get_elder_caregivers(db, alert.elder_id)
    for cg in caregivers:
        for ch in [NotificationChannel.SMS.value, NotificationChannel.CALL.value]:
            notif = Notification(
                alert_id=alert.id,
                recipient_id=cg.id,
                channel=ch,
                status=NotificationStatus.PENDING.value,
                attempt_count=0,
                next_attempt_at=now,
                payload=payload,
                created_at=now,
                updated_at=now,
            )
            db.add(notif)

    await db.commit()
    return True
