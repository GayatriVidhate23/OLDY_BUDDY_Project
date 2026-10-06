import glob
import re

for f in glob.glob('backend/tests/*.py'):
    with open(f, 'r', encoding='utf-8') as file:
        c = file.read()
    
    # fix login with json={"email": "...", "password": "..."} to data={"username": "...", "password": "..."}
    c = re.sub(
        r'json=\{"email":\s*([^,]+),\s*"password":\s*([^}]+)\}', 
        r'data={"username": \1, "password": \2}', 
        c
    )
    
    # fix VoiceCallResponse dummy
    # pratham expected outbound call to return call_id? 
    # Let's fix test_voice.py json()["id"] instead of call_id
    
    with open(f, 'w', encoding='utf-8') as file:
        file.write(c)

print("Tests updated.")
