import re

with open('backend/app/schemas.py', 'r', encoding='utf-8') as f:
    c = f.read()

c = re.sub(
    r'class VoiceCallCreate\(BaseModel\):\s*pass',
    'class VoiceCallCreate(BaseModel):\n    elder_id: int\n    call_type: str\n    status: str = "PENDING"',
    c
)

c = re.sub(
    r'class CallRecordResponse\(BaseModel\):\s*pass',
    'class CallRecordResponse(BaseModel):\n    id: int = 1',
    c
)

with open('backend/app/schemas.py', 'w', encoding='utf-8') as f:
    f.write(c)
