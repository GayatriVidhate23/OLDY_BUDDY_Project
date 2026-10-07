import pytest
import pytest_asyncio
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from app.models import User, ElderProfile, Reminder, Occurrence, ElderConsent, Event
from app.schemas import ReminderCreate
from app.services.scheduler import generate_occurrences, process_occurrences
from app.services.module4 import create_reminder
from sqlalchemy import select, func
from unittest.mock import AsyncMock

class FakeDeliveryProvider:
    def __init__(self):
        self.outcomes = {}
        
    async def deliver(self, occurrence_id: int, reminder: Reminder) -> str:
        if occurrence_id in self.outcomes:
            outcome = self.outcomes[occurrence_id].pop(0)
            if not self.outcomes[occurrence_id]:
                self.outcomes[occurrence_id] = [outcome]
            return outcome
        return "CONFIRMED"
        
    def set_outcome(self, occurrence_id: int, outcome_list: list):
        self.outcomes[occurrence_id] = outcome_list

@pytest_asyncio.fixture
async def elder_user(db):
    user = User(email="elder4@test.com", hashed_password="pwd", role="ELDER")
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    prof = ElderProfile(user_id=user.id, timezone="UTC", quiet_hours="22:00-06:00")
    db.add(prof)
    
    consent = ElderConsent(elder_id=user.id, kind="automated_calls")
    db.add(consent)
    await db.commit()
    
    return user

@pytest.mark.asyncio
async def test_scheduler_daily_3_times(elder_user, db):
    rem_in = ReminderCreate(
        title="Pills", kind="medication", recurrence="daily", times=["08:00", "14:00", "20:00"]
    )
    rem = await create_reminder(db, elder_user.id, rem_in)
    
    await generate_occurrences(db)
    
    res = await db.execute(select(func.count(Occurrence.id)).where(Occurrence.reminder_id == rem.id, Occurrence.status == "scheduled"))
    count = res.scalar()
    # 48 hours = 2-3 days generated
    assert count >= 6 # At least 2 days * 3 times
    
@pytest.mark.asyncio
async def test_scheduler_mwf(elder_user, db):
    rem_in = ReminderCreate(
        title="Gym", kind="activity", recurrence="weekdays", dates=["Monday", "Wednesday", "Friday"], times=["10:00"]
    )
    rem = await create_reminder(db, elder_user.id, rem_in)
    
    await generate_occurrences(db)
    
    res = await db.execute(select(Occurrence).where(Occurrence.reminder_id == rem.id))
    occs = res.scalars().all()
    for o in occs:
        # verify they land on MWF
        tz = timezone.utc
        dt_ny = o.due_at.replace(tzinfo=timezone.utc).astimezone(tz)
        assert dt_ny.strftime("%A") in ["Monday", "Wednesday", "Friday"]

@pytest.mark.asyncio
async def test_scheduler_end_date_cutoff(elder_user, db):
    now_ny = datetime.now(timezone.utc)
    tomorrow_ny = now_ny + timedelta(days=1)
    
    rem_in = ReminderCreate(
        title="Short term", kind="activity", recurrence="daily", times=["12:00"], 
        end_date=now_ny.strftime("%Y-%m-%d") # Ends today
    )
    rem = await create_reminder(db, elder_user.id, rem_in)
    
    await generate_occurrences(db)
    
    res = await db.execute(select(Occurrence).where(Occurrence.reminder_id == rem.id))
    occs = res.scalars().all()
    tz = timezone.utc
    for o in occs:
        dt_ny = o.due_at.replace(tzinfo=timezone.utc).astimezone(tz)
        assert dt_ny.date() <= now_ny.date()

@pytest.mark.asyncio
async def test_scheduler_appointment_offsets(elder_user, db):
    now_ny = datetime.now(timezone.utc)
    tomorrow = now_ny + timedelta(days=1)
    
    rem_in = ReminderCreate(
        title="Doctor", kind="appointment", recurrence="appointment", 
        dates=[tomorrow.strftime("%Y-%m-%d")], times=["15:00"]
    )
    rem = await create_reminder(db, elder_user.id, rem_in)
    
    await generate_occurrences(db)
    
    res = await db.execute(select(Occurrence).where(Occurrence.reminder_id == rem.id))
    occs = res.scalars().all()
    assert len(occs) == 2
    
    tz = timezone.utc
    dt1 = occs[0].due_at.replace(tzinfo=timezone.utc).astimezone(tz)
    dt2 = occs[1].due_at.replace(tzinfo=timezone.utc).astimezone(tz)
    
    # 24h before
    assert (dt1.date() == now_ny.date() and dt1.hour == 15) or (dt2.date() == now_ny.date() and dt2.hour == 15)
    # 1h before
    assert (dt1.date() == tomorrow.date() and dt1.hour == 14) or (dt2.date() == tomorrow.date() and dt2.hour == 14)

@pytest.mark.asyncio
async def test_worker_flow_dod(elder_user, db):
    # Definition of Done: NO_ANSWER × 3 → MISSED → exactly ONE reminder_missed event
    now_utc = datetime.now(timezone.utc).replace(tzinfo=None)
    
    rem_in = ReminderCreate(
        title="Important Pill", kind="medication", recurrence="one-off",
        dates=[now_utc.strftime("%Y-%m-%d")], times=["00:00"],
        max_attempts=3, retry_minutes=15
    )
    rem = await create_reminder(db, elder_user.id, rem_in)
    
    occ = Occurrence(reminder_id=rem.id, due_at=now_utc - timedelta(minutes=5), status="scheduled")
    db.add(occ)
    await db.commit()
    await db.refresh(occ)
    
    provider = FakeDeliveryProvider()
    provider.set_outcome(occ.id, ["NO_ANSWER", "NO_ANSWER", "NO_ANSWER"])
    
    # Attempt 1
    await process_occurrences(db, provider)
    await db.refresh(occ)
    assert occ.status == "awaiting_retry"
    assert occ.attempt_count == 1
    
    # Fast forward to next attempt
    occ.next_attempt_at = now_utc - timedelta(minutes=1)
    await db.commit()
    
    # Attempt 2
    await process_occurrences(db, provider)
    await db.refresh(occ)
    assert occ.status == "awaiting_retry"
    assert occ.attempt_count == 2
    
    # Fast forward again
    occ.next_attempt_at = now_utc - timedelta(minutes=1)
    await db.commit()
    
    # Attempt 3 -> MISSED
    await process_occurrences(db, provider)
    await db.refresh(occ)
    assert occ.status == "missed"
    assert occ.attempt_count == 3
    
    # Verify exactly one event
    res = await db.execute(select(Event).where(Event.elder_id == elder_user.id, Event.event_type == "reminder_missed"))
    events = res.scalars().all()
    assert len(events) == 1
    assert events[0].payload["occurrence_id"] == occ.id
