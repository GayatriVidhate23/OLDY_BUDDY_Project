from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, or_
from sqlalchemy.exc import IntegrityError
from app.models import Reminder, Occurrence, ElderProfile, ElderConsent, Event, Activity

def is_in_quiet_hours(due_tz: datetime, quiet_hours_str: str) -> bool:
    if not quiet_hours_str:
        return False
    try:
        start_str, end_str = quiet_hours_str.split('-')
        sh, sm = map(int, start_str.split(':'))
        eh, em = map(int, end_str.split(':'))
        
        start_time = due_tz.replace(hour=sh, minute=sm, second=0, microsecond=0)
        end_time = due_tz.replace(hour=eh, minute=em, second=0, microsecond=0)
        
        if start_time > end_time: # crosses midnight
            if due_tz >= start_time or due_tz <= end_time:
                return True
        else:
            if start_time <= due_tz <= end_time:
                return True
    except:
        pass
    return False

async def generate_occurrences(db: AsyncSession):
    # Next 48 hours
    now_utc = datetime.now(timezone.utc)
    horizon = now_utc + timedelta(hours=48)
    
    # Get active reminders
    res = await db.execute(select(Reminder).where(Reminder.is_active == True))
    reminders = res.scalars().all()
    
    for rem in reminders:
        # Get elder profile for timezone and quiet hours
        res_prof = await db.execute(select(ElderProfile).where(ElderProfile.user_id == rem.elder_id))
        prof = res_prof.scalar_one_or_none()
        if not prof:
            continue
            
        tz_name = prof.timezone if prof and prof.timezone else "UTC"
        tz = timezone.utc if tz_name == "UTC" else ZoneInfo(tz_name)
        
        # Check consent
        # Usually checking kind against ElderConsent
        res_consent = await db.execute(select(ElderConsent).where(ElderConsent.elder_id == rem.elder_id, ElderConsent.kind == "automated_calls", ElderConsent.revoked_at == None))
        has_consent = res_consent.scalar_one_or_none() is not None
        # if not has_consent, we will still generate but mark as cancelled
        
        now_tz = now_utc.astimezone(tz)
        horizon_tz = horizon.astimezone(tz)
        
        # Start date/end date constraints
        start_limit = now_tz
        if rem.start_date:
            sd = datetime.strptime(rem.start_date, "%Y-%m-%d").replace(tzinfo=tz)
            if sd > start_limit:
                start_limit = sd
                
        end_limit = horizon_tz
        if rem.end_date:
            ed = datetime.strptime(rem.end_date, "%Y-%m-%d").replace(tzinfo=tz)
            # Make end_date inclusive of the whole day
            ed = ed + timedelta(days=1) - timedelta(seconds=1)
            if ed < end_limit:
                end_limit = ed
                
        if start_limit > end_limit:
            continue
            
        # Determine due times in the window
        due_times = []
        
        # One-off / Appointments
        if rem.recurrence == "one-off" or rem.recurrence == "appointment":
            for d_str in rem.dates:
                for t_str in rem.times:
                    try:
                        dt_str = f"{d_str} {t_str}"
                        base_due = datetime.strptime(dt_str, "%Y-%m-%d %H:%M").replace(tzinfo=tz)
                        
                        if rem.recurrence == "appointment":
                            # Offsets: 1440, 60
                            due_times.append(base_due - timedelta(minutes=1440))
                            due_times.append(base_due - timedelta(minutes=60))
                        else:
                            due_times.append(base_due)
                    except:
                        pass
        elif rem.recurrence == "daily":
            # Generate for today, tomorrow, day after
            days = [now_tz.date(), (now_tz + timedelta(days=1)).date(), (now_tz + timedelta(days=2)).date()]
            for d in days:
                for t_str in rem.times:
                    try:
                        th, tm = map(int, t_str.split(':'))
                        due = datetime(d.year, d.month, d.day, th, tm, tzinfo=tz)
                        due_times.append(due)
                    except:
                        pass
        elif rem.recurrence == "weekdays":
            days = [now_tz.date(), (now_tz + timedelta(days=1)).date(), (now_tz + timedelta(days=2)).date()]
            for d in days:
                # Monday is 0, Sunday is 6. 
                # Dates array has weekday names like "Monday"
                weekday_name = d.strftime("%A")
                if weekday_name in rem.dates:
                    for t_str in rem.times:
                        try:
                            th, tm = map(int, t_str.split(':'))
                            due = datetime(d.year, d.month, d.day, th, tm, tzinfo=tz)
                            due_times.append(due)
                        except:
                            pass
                            
        for due_tz in due_times:
            if start_limit <= due_tz <= end_limit:
                due_utc = due_tz.astimezone(timezone.utc).replace(tzinfo=None)
                
                # Check if exists
                res_occ = await db.execute(select(Occurrence).where(Occurrence.reminder_id == rem.id, Occurrence.due_at == due_utc))
                if res_occ.scalar_one_or_none():
                    continue
                    
                status = "scheduled"
                reason = None
                
                if not has_consent:
                    status = "cancelled"
                    reason = "no_consent"
                elif is_in_quiet_hours(due_tz, prof.quiet_hours):
                    status = "cancelled"
                    reason = "quiet_hours"
                    
                occ = Occurrence(
                    reminder_id=rem.id,
                    due_at=due_utc,
                    status=status,
                    cancellation_reason=reason
                )
                db.add(occ)
                try:
                    await db.commit()
                except IntegrityError:
                    await db.rollback()

async def process_occurrences(db: AsyncSession, delivery_provider):
    now_utc = datetime.now(timezone.utc).replace(tzinfo=None)
    
    # 1. Recover stuck in_progress > 10 minutes
    stuck_limit = now_utc - timedelta(minutes=10)
    await db.execute(
        update(Occurrence)
        .where(Occurrence.status == "in_progress", Occurrence.last_attempt_at < stuck_limit)
        .values(status="awaiting_retry", next_attempt_at=now_utc)
    )
    await db.commit()
    
    # 2. Claim due scheduled or awaiting_retry
    # Using simplistic claiming logic since SQLite doesn't support SKIP LOCKED nicely
    res = await db.execute(
        select(Occurrence)
        .join(Reminder)
        .where(
            or_(
                and_(Occurrence.status == "scheduled", Occurrence.due_at <= now_utc),
                and_(Occurrence.status == "awaiting_retry", Occurrence.next_attempt_at <= now_utc)
            ),
            Reminder.is_active == True
        )
    )
    occurrences = res.scalars().all()
    
    for occ in occurrences:
        # Atomic claim by checking status
        res_claim = await db.execute(
            update(Occurrence)
            .where(Occurrence.id == occ.id, Occurrence.status.in_(["scheduled", "awaiting_retry"]))
            .values(status="in_progress", attempt_count=Occurrence.attempt_count + 1, last_attempt_at=now_utc)
        )
        await db.commit()
        
        if res_claim.rowcount == 0:
            continue # Claimed by another worker
            
        # Get reminder
        res_rem = await db.execute(select(Reminder).where(Reminder.id == occ.reminder_id))
        rem = res_rem.scalar_one()
        
        # Deliver via provider
        outcome = await delivery_provider.deliver(occ.id, rem)
        
        if outcome == "CONFIRMED" or outcome == "COMPLETED":
            occ.status = "completed"
            occ.completed_at = now_utc
            
            # Log activity
            act = Activity(elder_id=rem.elder_id, activity_type="REMINDER", description=f"Completed {rem.title}", status="COMPLETED")
            db.add(act)
        elif outcome == "NO_ANSWER" or outcome == "FAILED":
            if occ.attempt_count >= rem.max_attempts:
                occ.status = "missed"
                
                # Log missed activity
                act = Activity(elder_id=rem.elder_id, activity_type="REMINDER", description=f"Missed {rem.title}", status="MISSED")
                db.add(act)
                
                # Exactly one reminder_missed event
                # We can emit an Event here for escalation
                event = Event(elder_id=rem.elder_id, event_type="reminder_missed", payload={"reminder_id": rem.id, "occurrence_id": occ.id, "title": rem.title})
                db.add(event)
            else:
                occ.status = "awaiting_retry"
                occ.next_attempt_at = now_utc + timedelta(minutes=rem.retry_minutes)
        else:
            # Fallback
            occ.status = "awaiting_retry"
            occ.next_attempt_at = now_utc + timedelta(minutes=rem.retry_minutes)
            
        await db.commit()
