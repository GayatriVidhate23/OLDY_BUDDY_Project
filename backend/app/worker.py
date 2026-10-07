import asyncio
import logging
from app.database import AsyncSessionLocal
from app.services.notify.dispatcher import NotificationDispatcher
from app.decision_engine import escalate_alerts

logger = logging.getLogger(__name__)

async def notification_worker():
    dispatcher = NotificationDispatcher()
    logger.info("Starting background notification worker...")
    while True:
        try:
            async with AsyncSessionLocal() as db:
                await escalate_alerts(db)
                await dispatcher.process_outbox(db)
        except asyncio.CancelledError:
            logger.info("Notification worker cancelled.")
            break
        except Exception as e:
            logger.error(f"Worker error: {e}")
        
        await asyncio.sleep(5)
