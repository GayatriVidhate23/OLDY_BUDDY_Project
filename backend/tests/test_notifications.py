import pytest
from datetime import datetime, timedelta, timezone
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    User,
    UserRole,
    UserRelationship,
    RelationshipType,
    Alert,
    Notification,
    NotificationChannel,
    NotificationStatus,
    UserDevice,
)
from app.services.notify.policy import (
    create_alert_with_notifications,
    acknowledge_alert,
    escalate_emergency_alert,
)
from app.services.notify.dispatcher import NotificationDispatcher
from app.services.notify.expo_push import ExpoPushService
from app.services.notify.sms import SmsProvider

# --- Mock Providers for Tests ---
class FlakySmsProvider(SmsProvider):
    def __init__(self, fail_count: int):
        self.fail_count = fail_count
        self.attempts = 0

    async def send_sms(self, recipient_phone: str, message: str):
        self.attempts += 1
        if self.attempts <= self.fail_count:
            raise RuntimeError(f"Simulated SMS Provider Failure #{self.attempts}")
        return {"status": "success", "provider_message_id": f"flaky_sms_{self.attempts}"}

class AlwaysFailingSmsProvider(SmsProvider):
    async def send_sms(self, recipient_phone: str, message: str):
        raise RuntimeError("Permanent SMS Provider Network Failure")

# --- Test Cases ---

@pytest.mark.asyncio
async def test_transactional_alert_and_outbox_creation(db: AsyncSession):
    """
    Test 7: Alert + notification jobs are created transactionally in the same DB transaction.
    """
    # Setup Elder & Caregiver
    elder = User(email="t_elder@test.com", hashed_password="StrongPassword1!", role=UserRole.ELDER)
    caregiver = User(email="t_cg@test.com", hashed_password="StrongPassword1!", role=UserRole.CAREGIVER)
    db.add_all([elder, caregiver])
    await db.commit()
    await db.refresh(elder)
    await db.refresh(caregiver)

    rel = UserRelationship(elder_id=elder.id, caregiver_id=caregiver.id, type=RelationshipType.CAREGIVER)
    db.add(rel)
    await db.commit()

    # Create Alert with Notifications
    alert = await create_alert_with_notifications(
        db, elder_id=elder.id, severity="INFO", message="Elder check-in required"
    )

    # Verify Alert and Notification outbox records exist together
    assert alert.id is not None
    res = await db.execute(select(Notification).where(Notification.alert_id == alert.id))
    notifs = res.scalars().all()
    assert len(notifs) >= 1
    assert notifs[0].recipient_id == caregiver.id
    assert notifs[0].channel == NotificationChannel.PUSH.value
    assert notifs[0].status == NotificationStatus.PENDING.value

@pytest.mark.asyncio
async def test_policy_matrix_channels_and_recipients(db: AsyncSession):
    """
    Test 5: Policy matrix -> correct channels and recipients for INFO, WARNING, EMERGENCY.
    """
    elder = User(email="matrix_elder@test.com", hashed_password="StrongPassword1!", role=UserRole.ELDER)
    cg = User(email="matrix_cg@test.com", hashed_password="StrongPassword1!", role=UserRole.CAREGIVER)
    db.add_all([elder, cg])
    await db.commit()
    await db.refresh(elder)
    await db.refresh(cg)

    db.add(UserRelationship(elder_id=elder.id, caregiver_id=cg.id, type=RelationshipType.CAREGIVER))
    await db.commit()

    # 1. INFO Policy: Push immediately
    info_alert = await create_alert_with_notifications(db, elder.id, "INFO", "Routine update")
    res_info = await db.execute(select(Notification).where(Notification.alert_id == info_alert.id))
    info_notifs = res_info.scalars().all()
    assert len(info_notifs) == 1
    assert info_notifs[0].channel == NotificationChannel.PUSH.value

    # 2. WARNING Policy: Push immediately + Scheduled SMS (+15m)
    warn_alert = await create_alert_with_notifications(db, elder.id, "WARNING", "Missed medication", warning_delay_minutes=15)
    res_warn = await db.execute(select(Notification).where(Notification.alert_id == warn_alert.id))
    warn_notifs = res_warn.scalars().all()
    assert len(warn_notifs) == 2
    channels = {n.channel for n in warn_notifs}
    assert channels == {NotificationChannel.PUSH.value, NotificationChannel.SMS.value}

    # 3. EMERGENCY Policy: Push, SMS, and Call
    emerg_alert = await create_alert_with_notifications(db, elder.id, "EMERGENCY", "Fall detected!")
    res_emerg = await db.execute(select(Notification).where(Notification.alert_id == emerg_alert.id))
    emerg_notifs = res_emerg.scalars().all()
    assert len(emerg_notifs) == 3
    assert {n.channel for n in emerg_notifs} == {NotificationChannel.PUSH.value, NotificationChannel.SMS.value, NotificationChannel.CALL.value}

@pytest.mark.asyncio
async def test_provider_fails_twice_succeeds_on_attempt_3(db: AsyncSession):
    """
    Test 1: Provider fails twice -> succeeds on attempt 3.
    """
    user = User(email="flaky_user@test.com", hashed_password="StrongPassword1!", role=UserRole.CAREGIVER, phone_number="+15551234567")
    db.add(user)
    await db.commit()
    await db.refresh(user)

    now = datetime.now(timezone.utc)
    notif = Notification(
        recipient_id=user.id,
        channel=NotificationChannel.SMS.value,
        status=NotificationStatus.PENDING.value,
        attempt_count=0,
        next_attempt_at=now,
        payload={"body": "Test retry message"},
        created_at=now,
        updated_at=now,
    )
    db.add(notif)
    await db.commit()

    flaky_provider = FlakySmsProvider(fail_count=2)
    dispatcher = NotificationDispatcher(sms_provider=flaky_provider)

    # Attempt 1: Fails
    await dispatcher.process_outbox(db)
    await db.refresh(notif)
    assert notif.attempt_count == 1
    assert notif.status == NotificationStatus.PENDING.value
    assert "Failure #1" in notif.last_error

    # Force next_attempt_at to now for immediate test execution
    notif.next_attempt_at = datetime.now(timezone.utc) - timedelta(seconds=1)
    await db.commit()

    # Attempt 2: Fails
    await dispatcher.process_outbox(db)
    await db.refresh(notif)
    assert notif.attempt_count == 2
    assert notif.status == NotificationStatus.PENDING.value
    assert "Failure #2" in notif.last_error

    # Force next_attempt_at to now for immediate test execution
    notif.next_attempt_at = datetime.now(timezone.utc) - timedelta(seconds=1)
    await db.commit()

    # Attempt 3: Succeeds
    await dispatcher.process_outbox(db)
    await db.refresh(notif)
    assert notif.attempt_count == 3
    assert notif.status == NotificationStatus.SENT.value
    assert notif.provider_message_id == "flaky_sms_3"

@pytest.mark.asyncio
async def test_provider_always_fails_becomes_permanently_failed(db: AsyncSession):
    """
    Test 2: Provider always fails -> job becomes permanently failed.
    """
    user = User(email="failing_user@test.com", hashed_password="StrongPassword1!", role=UserRole.CAREGIVER, phone_number="+15551234567")
    db.add(user)
    await db.commit()
    await db.refresh(user)

    now = datetime.now(timezone.utc)
    notif = Notification(
        recipient_id=user.id,
        channel=NotificationChannel.SMS.value,
        status=NotificationStatus.PENDING.value,
        attempt_count=0,
        next_attempt_at=now,
        payload={"body": "Test permanent failure"},
        created_at=now,
        updated_at=now,
    )
    db.add(notif)
    await db.commit()

    dispatcher = NotificationDispatcher(sms_provider=AlwaysFailingSmsProvider())

    # Run dispatcher for max retries (3)
    for _ in range(3):
        notif.next_attempt_at = datetime.now(timezone.utc) - timedelta(seconds=1)
        await db.commit()
        await dispatcher.process_outbox(db)
        await db.refresh(notif)

    assert notif.attempt_count == 3
    assert notif.status == NotificationStatus.FAILED.value
    assert "Permanent SMS Provider Network Failure" in notif.last_error

@pytest.mark.asyncio
async def test_alert_acknowledged_pending_sms_skipped(db: AsyncSession):
    """
    Test 3: Alert acknowledged -> pending SMS is skipped.
    """
    elder = User(email="ack_elder@test.com", hashed_password="StrongPassword1!", role=UserRole.ELDER)
    cg = User(email="ack_cg@test.com", hashed_password="StrongPassword1!", role=UserRole.CAREGIVER)
    db.add_all([elder, cg])
    await db.commit()
    await db.refresh(elder)
    await db.refresh(cg)

    db.add(UserRelationship(elder_id=elder.id, caregiver_id=cg.id, type=RelationshipType.CAREGIVER))
    await db.commit()

    # Create WARNING alert (schedules SMS for +15m)
    alert = await create_alert_with_notifications(db, elder.id, "WARNING", "High heart rate", warning_delay_minutes=15)

    # Caregiver acknowledges the alert before SMS time
    await acknowledge_alert(db, alert.id, user_id=cg.id)

    # Force SMS notification time to ready
    sms_res = await db.execute(
        select(Notification).where(Notification.alert_id == alert.id, Notification.channel == NotificationChannel.SMS.value)
    )
    sms_notif = sms_res.scalar_one()
    sms_notif.next_attempt_at = datetime.now(timezone.utc) - timedelta(minutes=1)
    await db.commit()

    # Run Dispatcher
    dispatcher = NotificationDispatcher()
    await dispatcher.process_outbox(db)

    await db.refresh(sms_notif)
    assert sms_notif.status == NotificationStatus.SKIPPED.value

@pytest.mark.asyncio
async def test_device_not_registered_deactivates_token(db: AsyncSession):
    """
    Test 4: DeviceNotRegistered -> device token is deactivated (is_active = False).
    """
    user = User(email="device_user@test.com", hashed_password="StrongPassword1!", role=UserRole.CAREGIVER)
    db.add(user)
    await db.commit()
    await db.refresh(user)

    bad_token = "ExponentPushToken[INVALID_TOKEN_123]"
    device = UserDevice(user_id=user.id, push_token=bad_token, is_active=True)
    db.add(device)
    await db.commit()

    # Mock Expo Service returning DeviceNotRegistered
    class MockExpoPushService(ExpoPushService):
        async def send_push_notifications(self, db_sess, messages):
            await self.deactivate_device_token(db_sess, bad_token)
            return [{"token": bad_token, "status": "error", "error": "DeviceNotRegistered"}]

    dispatcher = NotificationDispatcher(push_service=MockExpoPushService())
    
    now = datetime.now(timezone.utc)
    notif = Notification(
        recipient_id=user.id,
        channel=NotificationChannel.PUSH.value,
        status=NotificationStatus.PENDING.value,
        attempt_count=0,
        next_attempt_at=now,
        payload={"body": "Test push deactivation"},
        created_at=now,
        updated_at=now,
    )
    db.add(notif)
    await db.commit()

    await dispatcher.process_outbox(db)
    await db.refresh(device)
    assert device.is_active is False

@pytest.mark.asyncio
async def test_emergency_escalation_continues_after_notification_failure(db: AsyncSession):
    """
    Test 6: Emergency escalation continues after SMS/call failure.
    A permanently failed SMS or call MUST NEVER stop emergency escalation.
    """
    elder = User(email="esc_elder@test.com", hashed_password="StrongPassword1!", role=UserRole.ELDER)
    cg = User(email="esc_cg@test.com", hashed_password="StrongPassword1!", role=UserRole.CAREGIVER)
    db.add_all([elder, cg])
    await db.commit()
    await db.refresh(elder)
    await db.refresh(cg)

    db.add(UserRelationship(elder_id=elder.id, caregiver_id=cg.id, type=RelationshipType.CAREGIVER))
    await db.commit()

    # Create EMERGENCY alert
    alert = await create_alert_with_notifications(db, elder.id, "EMERGENCY", "SOS Alert")

    # Fail all Stage 1 notifications using AlwaysFailingSmsProvider
    dispatcher = NotificationDispatcher(sms_provider=AlwaysFailingSmsProvider())
    for _ in range(3):
        # Reset ready times for immediate retry in test
        res = await db.execute(select(Notification).where(Notification.alert_id == alert.id))
        for n in res.scalars().all():
            n.next_attempt_at = datetime.now(timezone.utc) - timedelta(seconds=1)
        await db.commit()
        await dispatcher.process_outbox(db)

    # Verify stage 1 notifications failed
    res_failed = await db.execute(
        select(Notification).where(Notification.alert_id == alert.id, Notification.channel == NotificationChannel.SMS.value)
    )
    failed_sms = res_failed.scalar_one()
    assert failed_sms.status == NotificationStatus.FAILED.value

    # Perform Emergency Escalation -> MUST STILL PROCEED to Stage 2 regardless of notification failures!
    escalated = await escalate_emergency_alert(db, alert.id)
    assert escalated is True
    
    await db.refresh(alert)
    assert alert.escalation_stage == 2
    assert alert.escalation_status == "ESCALATED"
