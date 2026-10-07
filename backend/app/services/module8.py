import datetime
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc

from app.models import Activity, Event, Alert, Message, User
from app.schemas import ElderStatusResponse, TrendsResponse, TrendDay

async def get_elder_status(db: AsyncSession, elder_id: int) -> ElderStatusResponse:
    # Check for active alerts
    active_alerts = await db.execute(
        select(Alert).where(Alert.elder_id == elder_id, Alert.status == "open")
    )
    alerts = active_alerts.scalars().all()
    
    if any(a.severity in ["EMERGENCY", "HIGH"] for a in alerts):
        return ElderStatusResponse(status="Emergency", headline="Immediate attention needed")
        
    if any(a.severity == "WARNING" for a in alerts):
        return ElderStatusResponse(status="Warning", headline="Some issues require attention")
        
    if alerts:
        return ElderStatusResponse(status="Attention", headline="There are active alerts")
        
    # Check activities today
    today_start = datetime.datetime.now(datetime.timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    
    activities_res = await db.execute(
        select(Activity).where(Activity.elder_id == elder_id, Activity.timestamp >= today_start)
    )
    activities = activities_res.scalars().all()
    
    if not activities:
        return ElderStatusResponse(status="Unknown", headline="No sufficient activity to report status")
        
    if any(a.status == "MISSED" for a in activities):
        return ElderStatusResponse(status="Warning", headline="Missed tasks detected today")
        
    return ElderStatusResponse(status="Normal", headline="Mom is doing okay today")

async def get_elder_trends(db: AsyncSession, elder_id: int, days: int) -> TrendsResponse:
    today = datetime.datetime.now(datetime.timezone.utc).date()
    start_date = today - datetime.timedelta(days=days - 1)
    
    res = await db.execute(
        select(Activity).where(
            Activity.elder_id == elder_id, 
            Activity.timestamp >= datetime.datetime.combine(start_date, datetime.time.min).replace(tzinfo=datetime.timezone.utc)
        )
    )
    activities = res.scalars().all()
    
    trends_dict = {}
    for i in range(days):
        d = start_date + datetime.timedelta(days=i)
        trends_dict[d.isoformat()] = {
            "reminders_completed": 0,
            "reminders_missed": 0,
            "checkins_completed": 0,
            "checkins_missed": 0,
            "conversations": 0
        }
        
    for a in activities:
        d_str = a.timestamp.date().isoformat()
        if d_str in trends_dict:
            if a.activity_type == "REMINDER":
                if a.status == "COMPLETED":
                    trends_dict[d_str]["reminders_completed"] += 1
                elif a.status == "MISSED":
                    trends_dict[d_str]["reminders_missed"] += 1
            elif a.activity_type == "CHECK_IN":
                if a.status == "COMPLETED":
                    trends_dict[d_str]["checkins_completed"] += 1
                elif a.status == "MISSED":
                    trends_dict[d_str]["checkins_missed"] += 1
            elif a.activity_type == "CONVERSATION":
                trends_dict[d_str]["conversations"] += 1
                
    trend_days = [
        TrendDay(
            date=d_str,
            reminders_completed=stats["reminders_completed"],
            reminders_missed=stats["reminders_missed"],
            checkins_completed=stats["checkins_completed"],
            checkins_missed=stats["checkins_missed"],
            conversations=stats["conversations"]
        ) for d_str, stats in trends_dict.items()
    ]
    trend_days.sort(key=lambda x: x.date)
    return TrendsResponse(days=trend_days)

async def send_message(db: AsyncSession, elder_id: int, sender_user_id: int, sender_role: str, body: str, kind: str) -> Message:
    if len(body) > 500:
        raise ValueError("Message body must be 500 characters or less")
    
    msg = Message(
        elder_id=elder_id,
        sender_user_id=sender_user_id,
        sender_role=sender_role,
        body=body,
        kind=kind
    )
    db.add(msg)
    await db.commit()
    await db.refresh(msg)
    
    # If quick reply "Please call me", create an alert
    if body.strip().lower() == "please call me":
        alert = Alert(
            elder_id=elder_id,
            severity="HIGH",
            title=f"{sender_role.capitalize()} requested a call: 'Please call me'"
        )
        db.add(alert)
        await db.commit()
        
    return msg

async def get_messages(db: AsyncSession, elder_id: int, user_id: int, user_role: str, limit: int = 50) -> List[Message]:
    # Mark opposite-side messages as read
    unreads = await db.execute(
        select(Message).where(
            Message.elder_id == elder_id,
            Message.sender_user_id != user_id,
            Message.read_at == None
        )
    )
    unreads_list = unreads.scalars().all()
    for msg in unreads_list:
        msg.read_at = datetime.datetime.now(datetime.timezone.utc)
    if unreads_list:
        await db.commit()
    
    res = await db.execute(
        select(Message).where(Message.elder_id == elder_id).order_by(desc(Message.created_at)).limit(limit)
    )
    return res.scalars().all()
