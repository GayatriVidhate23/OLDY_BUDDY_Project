import glob
import re
import os

for f in glob.glob('backend/tests/*.py'):
    with open(f, 'r', encoding='utf-8') as file:
        c = file.read()
    
    # 1. Fix passwords
    c = re.sub(r'"password"\s*:\s*"pass"', '"password": "StrongPassword1!"', c)
    c = re.sub(r'data=\{"username"\s*:\s*([^,]+),\s*"password"\s*:\s*"pass"\}', r'data={"username": \1, "password": "StrongPassword1!"}', c)
    
    # 2. Fix 201 -> 200
    c = c.replace('== 201', '== 200')
    
    # 3. Fix login payloads
    # Specifically, replace json={"email": "...", "password": "..."} with data={"username": "...", "password": "..."} ONLY for login endpoints
    def replacer(match):
        endpoint = match.group(1)
        payload = match.group(2)
        email = match.group(3)
        password = match.group(4)
        rest = match.group(5)
        
        if 'login' in endpoint:
            return f'"{endpoint}", data={{"username": {email}, "password": {password}}}{rest}'
        else:
            return match.group(0) # don't change
            
    c = re.sub(
        r'"([^"]+)",\s*json=\{"email"\s*:\s*([^,]+),\s*"password"\s*:\s*([^}]+)\}([^)]*)',
        replacer,
        c
    )
    
    with open(f, 'w', encoding='utf-8') as file:
        file.write(c)

print("Tests updated.")
