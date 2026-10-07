"""
Expo Push Notification Service for Oldy Buddy.

iOS Time-Sensitive & Critical Alert Configuration Notes:
--------------------------------------------------------
- For iOS Time-Sensitive notifications, include `interruptionLevel: 'time-sensitive'` in the push payload.
- For iOS Critical Alerts (which play a sound even when Do Not Disturb is ON or the physical switch is muted):
  1. Your Apple Developer Account must be granted the Critical Alerts entitlement by Apple.
  2. Add `com.apple.developer.usernotifications.critical-alerts` to your iOS App entitlements configuration.
  3. Include `sound: { critical: True, name: 'default', volume: 1.0 }` in the Expo Push message payload.
"""

import httpx
from typing import List, Dict, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import settings
from app.models import UserDevice

EXPO_PUSH_URL = getattr(settings, "EXPO_PUSH_TOKEN_URL", "https://exp.host/--/api/v2/push/send")
MAX_BATCH_SIZE = 100

class ExpoPushService:
    def __init__(self, api_url: str = None):
        self.api_url = api_url or EXPO_PUSH_URL

    async def send_push_notifications(
        self, db: AsyncSession, messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Sends push notification messages in batches of max 100 to Expo Push API.
        Handles tickets/receipts and deactivates tokens with 'DeviceNotRegistered'.
        """
        if not messages:
            return []

        results = []
        # Process in chunks of 100 max
        for i in range(0, len(messages), MAX_BATCH_SIZE):
            chunk = messages[i : i + MAX_BATCH_SIZE]
            
            # Ensure Android channel and priority settings are present
            for msg in chunk:
                msg.setdefault("channelId", "alerts")
                msg.setdefault("priority", "high")
                msg.setdefault("sound", "default")

            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.post(
                        self.api_url,
                        json=chunk,
                        headers={
                            "Accept": "application/json",
                            "Accept-Encoding": "gzip, deflate",
                            "Content-Type": "application/json",
                        },
                    )
                    
                if resp.status_code == 200:
                    data = resp.json().get("data", [])
                    for idx, ticket in enumerate(data):
                        push_token = chunk[idx].get("to")
                        status = ticket.get("status")

                        if status == "ok":
                            results.append({"token": push_token, "status": "ok", "id": ticket.get("id")})
                        else:
                            error_code = ticket.get("details", {}).get("error") or ticket.get("message")
                            # Handle DeviceNotRegistered by deactivating device
                            if error_code == "DeviceNotRegistered" or "DeviceNotRegistered" in str(ticket):
                                await self.deactivate_device_token(db, push_token)

                            results.append({
                                "token": push_token,
                                "status": "error",
                                "error": error_code,
                            })
                else:
                    results.append({"status": "error", "error": f"HTTP {resp.status_code}: {resp.text}"})

            except Exception as e:
                results.append({"status": "error", "error": str(e)})

        return results

    async def deactivate_device_token(self, db: AsyncSession, push_token: str) -> None:
        """
        Deactivates a device when Expo returns DeviceNotRegistered error.
        """
        if not push_token:
            return
        res = await db.execute(select(UserDevice).where(UserDevice.push_token == push_token))
        devices = res.scalars().all()
        for dev in devices:
            dev.is_active = False
        if devices:
            await db.commit()
