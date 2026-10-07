content = """
# --- Module 4 Endpoints ---
from app.schemas import ReminderCreate, ReminderUpdate, ReminderResponse, OccurrenceResponse
from app.services.module4 import (
    create_reminder, get_reminders, update_reminder, delete_reminder, get_today_reminders, ack_occurrence
)

@router.post("/v1/elders/{elder_id}/reminders", response_model=ReminderResponse)
async def api_create_reminder(elder_id: int, rem_in: ReminderCreate, db: AsyncSession = Depends(get_db), _: bool = Depends(verify_elder_access)):
    return await create_reminder(db, elder_id, rem_in)

@router.get("/v1/elders/{elder_id}/reminders", response_model=List[ReminderResponse])
async def api_get_reminders(elder_id: int, db: AsyncSession = Depends(get_db), _: bool = Depends(verify_elder_access)):
    return await get_reminders(db, elder_id)

@router.patch("/v1/elders/{elder_id}/reminders/{rid}", response_model=ReminderResponse)
async def api_update_reminder(elder_id: int, rid: int, rem_in: ReminderUpdate, db: AsyncSession = Depends(get_db), _: bool = Depends(verify_elder_access)):
    rem = await update_reminder(db, elder_id, rid, rem_in)
    if not rem:
        raise HTTPException(status_code=404, detail="Reminder not found")
    return rem

@router.delete("/v1/elders/{elder_id}/reminders/{rid}")
async def api_delete_reminder(elder_id: int, rid: int, db: AsyncSession = Depends(get_db), _: bool = Depends(verify_elder_access)):
    success = await delete_reminder(db, elder_id, rid)
    if not success:
        raise HTTPException(status_code=404, detail="Reminder not found")
    return {"msg": "Deleted"}

@router.get("/v1/elders/{elder_id}/reminders/today", response_model=List[OccurrenceResponse])
async def api_get_today_reminders(elder_id: int, db: AsyncSession = Depends(get_db), _: bool = Depends(verify_elder_access)):
    return await get_today_reminders(db, elder_id)

@router.post("/v1/occurrences/{oid}/ack", response_model=OccurrenceResponse)
async def api_ack_occurrence(oid: int, db: AsyncSession = Depends(get_db)):
    occ = await ack_occurrence(db, oid)
    if not occ:
        raise HTTPException(status_code=404, detail="Occurrence not found")
    return occ
"""
with open("app/api.py", "a", encoding="utf-8") as f:
    f.write(content)
