import re
with open('backend/app/schemas.py', 'r', encoding='utf-8') as f:
    c = f.read()
c = re.sub(r'device_type:\s*Optional\[str\]\s*=\s*\\?[\r\n]+android\\?[\r\n]*', 'device_type: Optional[str] = "android"\n', c)
with open('backend/app/schemas.py', 'w', encoding='utf-8') as f:
    f.write(c)
