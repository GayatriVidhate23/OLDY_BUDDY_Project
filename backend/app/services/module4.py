from typing import List, Optional
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, update, delete, func, or_
from app.models import Reminder, Occurrence, ElderProfile, Alert, Event
from app.schemas import ReminderCreate, ReminderUpdate
from zoneinfo import ZoneInfo

async def create_reminder(db: AsyncSession, elder_id: int, rem_in: ReminderCreate) -> Reminder:
    rem = Reminder(
        elder_id=elder_id,
        title=rem_in.title,
        kind=rem_in.kind,
        recurrence=rem_in.recurrence,
        times=rem_in.times,
        dates=rem_in.dates,
        start_date=rem_in.start_date,
        end_date=rem_in.end_date,
        max_attempts=rem_in.max_attempts,
        retry_minutes=rem_in.retry_minutes,
        is_active=True
    )
    db.add(rem)
    await db.commit()
    await db.refresh(rem)
    return rem

async def get_reminders(db: AsyncSession, elder_id: int) -> List[Reminder]:
    res = await db.execute(select(Reminder).where(Reminder.elder_id == elder_id, Reminder.is_active == True))
    return list(res.scalars().all())

async def update_reminder(db: AsyncSession, elder_id: int, rid: int, rem_in: ReminderUpdate) -> Reminder:
    res = await db.execute(select(Reminder).where(Reminder.id == rid, Reminder.elder_id == elder_id))
    rem = res.scalar_one_or_none()
    if not rem:
        return None
    
    update_data = rem_in.model_dump(exclude_unset=True)
    for k, v in update_data.items():
        setattr(rem, k, v)
        
    await db.commit()
    
    # Cancel future scheduled occurrences
    await db.execute(
        update(Occurrence)
        .where(Occurrence.reminder_id == rid, Occurrence.status == "scheduled", Occurrence.due_at > datetime.now(timezone.utc))
        .values(status="cancelled", cancellation_reason="reminder_updated")
    )
    await db.commit()
    await db.refresh(rem)
    return rem

async def delete_reminder(db: AsyncSession, elder_id: int, rid: int) -> bool:
    res = await db.execute(select(Reminder).where(Reminder.id == rid, Reminder.elder_id == elder_id))
    rem = res.scalar_one_or_none()
    if not rem:
        return False
        
    rem.is_active = False
    await db.commit()
    
    # Cancel future scheduled occurrences
    await db.execute(
        update(Occurrence)
        .where(Occurrence.reminder_id == rid, Occurrence.status == "scheduled", Occurrence.due_at > datetime.now(timezone.utc))
        .values(status="cancelled", cancellation_reason="reminder_deleted")
    )
    await db.commit()
    return True

async def get_today_reminders(db: AsyncSession, elder_id: int) -> List[Occurrence]:
    res = await db.execute(select(ElderProfile).where(ElderProfile.user_id == elder_id))
    prof = res.scalar_one_or_none()
    tz_name = prof.timezone if prof and prof.timezone else "UTC"
    tz = ZoneInfo(tz_name)
    
    now_tz = datetime.now(tz)
    start_of_day = datetime(now_tz.year, now_tz.month, now_tz.day, tzinfo=tz).astimezone(timezone.utc)
    end_of_day = start_of_day + timedelta(days=1)
    
    res = await db.execute(
        select(Occurrence)
        .join(Reminder)
        .where(
            Reminder.elder_id == elder_id,
            Occurrence.due_at >= start_of_day,
            Occurrence.due_at < end_of_day
        )
        .order_by(Occurrence.due_at.asc())
    )
    return list(res.scalars().all())

async def ack_occurrence(db: AsyncSession, oid: int) -> Occurrence:
    res = await db.execute(select(Occurrence).where(Occurrence.id == oid))
    occ = res.scalar_one_or_none()
    if not occ:
        return None
        
    occ.status = "completed"
    occ.completed_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(occ)
    return occ
