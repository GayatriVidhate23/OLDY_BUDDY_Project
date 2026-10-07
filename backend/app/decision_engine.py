
from datetime import datetime, timedelta, timezone
from app.models import Event, Alert, Notification, EmergencyContact
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.services.notify.policy import get_elder_caregivers

EVENT_TYPES = [
    "reminder_completed", "reminder_declined", "reminder_missed",
    "checkin_completed", "checkin_missed", "checkin_concern",
    "wellbeing_concern", "emergency_phrase", "sos_pressed",
    "sos_cancelled", "call_completed", "call_no_answer",
    "food_request", "alert_acknowledged", "alert_resolved"
]

def determine_alert(event_type: str, elder_id: int, event_id: int) -> dict:
    # Pure deterministic rules
    if event_type in ["sos_pressed", "emergency_phrase"]:
        return {"severity": "EMERGENCY", "title": "Emergency indicators detected", "escalate": True}
    if event_type in ["checkin_missed", "checkin_concern", "wellbeing_concern"]:
        return {"severity": "WARNING", "title": "Verification required", "escalate": False}
    if event_type == "reminder_missed":
        return {"severity": "INFO", "title": "Possible missed reminder", "escalate": False}
    return None

async def process_event(db: AsyncSession, elder_id: int, event_type: str, source: str = None, payload: dict = None) -> Event:
    event = Event(elder_id=elder_id, event_type=event_type, source=source, payload=payload or {})
    db.add(event)
    await db.flush() # get id

    if event_type == "sos_cancelled":
        # Resolve related open SOS alerts
        res = await db.execute(select(Alert).where(Alert.elder_id == elder_id, Alert.status.in_(["open", "acknowledged"]), Alert.title == "Emergency indicators detected"))
        for alert in res.scalars().all():
            alert.status = "resolved"
            alert.resolved_at = datetime.now(timezone.utc)
            alert.resolution = "Elder verified safe"

    decision = determine_alert(event_type, elder_id, event.id)
    if decision:
        # Check uniqueness to prevent duplicates
        res = await db.execute(select(Alert).where(Alert.elder_id == elder_id, Alert.status == "open", Alert.title == decision["title"]))
        if not res.scalar_one_or_none():
            alert = Alert(
                elder_id=elder_id,
                severity=decision["severity"],
                title=decision["title"],
                details=f"Triggered by {event_type}",
                source_event_id=event.id,
                status="open",
                escalation_stage=0 if decision["escalate"] else -1,
                next_escalation_time=datetime.now(timezone.utc) + timedelta(seconds=90) if decision["escalate"] else None
            )
            db.add(alert)
            await db.flush()
            
            # Basic policies
            caregivers = await get_elder_caregivers(db, elder_id)
            if decision["severity"] == "INFO":
                for cg in caregivers:
                    job = Notification(channel="PUSH", recipient_id=cg.id, alert_id=alert.id, payload={"msg": alert.title})
                    db.add(job)
            elif decision["severity"] == "WARNING":
                for cg in caregivers:
                    job = Notification(channel="PUSH", recipient_id=cg.id, alert_id=alert.id, payload={"msg": alert.title})
                    db.add(job)
                    job2 = Notification(channel="SMS", recipient_id=cg.id, alert_id=alert.id, payload={"msg": alert.title}, next_attempt_at=datetime.now(timezone.utc) + timedelta(minutes=15))
                    db.add(job2)
    return event

async def escalate_alerts(db: AsyncSession, current_time: datetime = None):
    if not current_time:
        current_time = datetime.now(timezone.utc)
        
    res = await db.execute(select(Alert).where(Alert.status == "open", Alert.next_escalation_time <= current_time))
    alerts = res.scalars().all()
    
    for alert in alerts:
        if alert.escalation_stage == 0:
            alert.escalation_stage = 1
            alert.next_escalation_time = current_time + timedelta(seconds=180)
            caregivers = await get_elder_caregivers(db, alert.elder_id)
            for cg in caregivers:
                db.add(Notification(channel="PUSH", recipient_id=cg.id, alert_id=alert.id, payload={"msg": "URGENT", "priority": "high"}))
                db.add(Notification(channel="SMS", recipient_id=cg.id, alert_id=alert.id, payload={"msg": "URGENT ALARM"}))
                db.add(Notification(channel="CALL", recipient_id=cg.id, alert_id=alert.id, payload={"msg": "Automated call"}))
        elif alert.escalation_stage == 1:
            alert.escalation_stage = 2
            alert.next_escalation_time = current_time + timedelta(minutes=5)
            # Find emergency contacts
            res_ec = await db.execute(select(EmergencyContact).where(EmergencyContact.elder_id == alert.elder_id))
            ecs = res_ec.scalars().all()
            for ec in ecs:
                db.add(Notification(channel="SMS", recipient_phone=ec.phone_e164, alert_id=alert.id, payload={"msg": "URGENT: Caregivers unreachable"}))
        elif alert.escalation_stage >= 2 and alert.escalation_stage < 8:
            # Stage 3 paging
            alert.escalation_stage += 1
            alert.next_escalation_time = current_time + timedelta(minutes=5)
            caregivers = await get_elder_caregivers(db, alert.elder_id)
            for cg in caregivers:
                db.add(Notification(channel="PUSH", recipient_id=cg.id, alert_id=alert.id, payload={"msg": "Call 112"}))
        elif alert.escalation_stage >= 8:
            alert.next_escalation_time = None
