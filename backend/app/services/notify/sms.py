"""
SMS Service for Oldy Buddy Notifications.

India DLT (Distributed Ledger Technology) & Plivo Sender ID / Template Requirements:
-------------------------------------------------------------------------------------
1. Telecom Regulatory Authority of India (TRAI) Mandate:
   - All commercial SMS sent to Indian phone numbers (+91) must be routed through a registered DLT entity.
2. DLT Entity Registration:
   - Register your business entity on an official DLT portal (e.g. Jio DLT, Vodafone DLT, Airtel DLT).
3. Header / Sender ID Registration:
   - Register a 6-character alphabetic Header (Sender ID) (e.g. `OLDYBD`) on the DLT portal for transactional alerts.
4. Content Template Registration:
   - Register exact SMS message templates (with variable placeholders like `{#var#}`) on DLT.
   - Obtain a unique `dlt_entity_id` and `dlt_template_id` for each approved template.
5. Plivo Integration for DLT:
   - When sending SMS via Plivo API to Indian numbers, pass `dlt_entity_id` and `dlt_template_id` parameters in the request payload.
6. Plivo KYC Requirements:
   - Plivo requires account KYC verification (address proof, company registration, ID) before allocating phone numbers or enabling SMS dispatch.
"""

import httpx
from abc import ABC, abstractmethod
from typing import Dict, Any, List
from app.database import settings

class SmsProvider(ABC):
    @abstractmethod
    async def send_sms(self, recipient_phone: str, message: str) -> Dict[str, Any]:
        pass

class ConsoleSmsProvider(SmsProvider):
    """
    Console / Mock SMS provider for development and testing.
    Stores sent messages in memory for test assertion.
    """
    def __init__(self):
        self.sent_messages: List[Dict[str, str]] = []

    async def send_sms(self, recipient_phone: str, message: str) -> Dict[str, Any]:
        record = {"phone": recipient_phone, "message": message}
        self.sent_messages.append(record)
        print(f"[CONSOLE SMS] Sent to {recipient_phone}: {message}")
        return {
            "status": "success",
            "provider_message_id": f"mock_sms_{len(self.sent_messages)}",
            "phone": recipient_phone,
        }

class PlivoSmsProvider(SmsProvider):
    """
    Production Plivo SMS API Provider.
    """
    def __init__(self, auth_id: str = None, auth_token: str = None, sender_id: str = None):
        self.auth_id = auth_id or getattr(settings, "PLIVO_AUTH_ID", "")
        self.auth_token = auth_token or getattr(settings, "PLIVO_AUTH_TOKEN", "")
        self.sender_id = sender_id or getattr(settings, "PLIVO_SENDER_ID", "OLDYBUDDY")
        self.api_url = f"https://api.plivo.com/v1/Account/{self.auth_id}/Message/"

    async def send_sms(self, recipient_phone: str, message: str) -> Dict[str, Any]:
        if not self.auth_id or not self.auth_token:
            raise ValueError("Plivo credentials (PLIVO_AUTH_ID, PLIVO_AUTH_TOKEN) are not configured!")

        payload = {
            "src": self.sender_id,
            "dst": recipient_phone,
            "text": message,
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                self.api_url,
                auth=(self.auth_id, self.auth_token),
                json=payload,
            )

        if resp.status_code in [200, 202]:
            data = resp.json()
            message_uuid = data.get("message_uuid", [None])[0] or "plivo_sent"
            return {"status": "success", "provider_message_id": message_uuid}
        else:
            raise RuntimeError(f"Plivo SMS API Error (HTTP {resp.status_code}): {resp.text}")

def get_sms_provider() -> SmsProvider:
    provider_type = getattr(settings, "NOTIFY_PROVIDER_TYPE", "console").lower()
    if provider_type == "plivo":
        return PlivoSmsProvider()
    return ConsoleSmsProvider()
