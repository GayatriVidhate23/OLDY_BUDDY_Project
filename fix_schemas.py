import re

with open('backend/app/schemas.py', 'r', encoding='utf-8') as f:
    c = f.read()

dummy_classes = """
class OutboundCallRequest(BaseModel):
    elder_id: int
    call_type: str

class VoiceWebhookRequest(BaseModel):
    user_speech: str = ""
    call_id: str = ""
    event_type: str = ""

class VoiceCallResponse(BaseModel):
    id: int = 1
    elder_id: int = 1
    status: str = "completed"

class AlertResponse(BaseModel):
    id: int = 1
    elder_id: int = 1
    alert_type: str = "SOS"
    status: str = "PENDING"
    title: str = "Alert"
    message: str = "Alert message"
"""

c = re.sub(r'class OutboundCallRequest\(BaseModel\): pass', '', c)
c = re.sub(r'class VoiceWebhookRequest\(BaseModel\): pass', '', c)
c = re.sub(r'class VoiceCallResponse\(BaseModel\): pass', '', c)
c = re.sub(r'class AlertResponse\(BaseModel\): pass', '', c)

c += dummy_classes

with open('backend/app/schemas.py', 'w', encoding='utf-8') as f:
    f.write(c)
