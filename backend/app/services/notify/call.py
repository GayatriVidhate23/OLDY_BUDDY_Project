import httpx
from abc import ABC, abstractmethod
from typing import Dict, Any, List
from app.database import settings

class CallProvider(ABC):
    @abstractmethod
    async def make_call(self, recipient_phone: str, message: str) -> Dict[str, Any]:
        pass

class ConsoleCallProvider(CallProvider):
    def __init__(self):
        self.made_calls: List[Dict[str, str]] = []

    async def make_call(self, recipient_phone: str, message: str) -> Dict[str, Any]:
        record = {"phone": recipient_phone, "message": message}
        self.made_calls.append(record)
        print(f"[CONSOLE CALL] Calling {recipient_phone}, message: {message}")
        return {
            "status": "success",
            "provider_message_id": f"mock_call_{len(self.made_calls)}",
        }

class PlivoCallProvider(CallProvider):
    def __init__(self, auth_id: str = None, auth_token: str = None, caller_id: str = None, answer_url: str = None):
        self.auth_id = auth_id or getattr(settings, "PLIVO_AUTH_ID", "")
        self.auth_token = auth_token or getattr(settings, "PLIVO_AUTH_TOKEN", "")
        self.caller_id = caller_id or getattr(settings, "PLIVO_CALLER_ID", "+15550000000")
        self.answer_url = answer_url or getattr(settings, "PLIVO_ANSWER_URL", "https://s3.amazonaws.com/static.plivo.com/answer.xml")
        self.api_url = f"https://api.plivo.com/v1/Account/{self.auth_id}/Call/"

    async def make_call(self, recipient_phone: str, message: str) -> Dict[str, Any]:
        if not self.auth_id or not self.auth_token:
            raise ValueError("Plivo credentials are not configured!")

        # Basic integration: making an outbound call with a static answer URL.
        # Plivo XML could dynamically read the message using a webhook, but static Answer URL serves for baseline MVP integration.
        payload = {
            "to": recipient_phone,
            "from": self.caller_id,
            "answer_url": self.answer_url,
            "answer_method": "GET"
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                self.api_url,
                auth=(self.auth_id, self.auth_token),
                json=payload,
            )

        if resp.status_code in [200, 201]:
            data = resp.json()
            request_uuid = data.get("request_uuid") or "plivo_call_sent"
            return {"status": "success", "provider_message_id": request_uuid}
        else:
            raise RuntimeError(f"Plivo Call API Error (HTTP {resp.status_code}): {resp.text}")

def get_call_provider() -> CallProvider:
    provider_type = getattr(settings, "NOTIFY_PROVIDER_TYPE", "console").lower()
    if provider_type == "plivo":
        return PlivoCallProvider()
    return ConsoleCallProvider()
