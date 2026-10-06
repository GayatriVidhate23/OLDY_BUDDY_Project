import glob
import re

for f in glob.glob('backend/tests/*.py'):
    with open(f, 'r', encoding='utf-8') as file:
        c = file.read()
    
    # 1. Strip /v1 from all test endpoints
    c = c.replace('"/api/v1/', '"/api/')
    c = c.replace('f"/api/v1/', 'f"/api/')
    
    # 2. Fix test_elders.py PUT /elders/{elder_id} to POST /elders/{elder_id}/profile
    c = c.replace('client.put(\n        f"/api/elders/{elder_id}",', 'client.post(\n        f"/api/elders/{elder_id}/profile",')
    
    # 3. Check for any other test_voice endpoints
    c = c.replace('/voice/outbound-call', '/voice/outbound')
    
    with open(f, 'w', encoding='utf-8') as file:
        file.write(c)

print("v1 stripped.")
