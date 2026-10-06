import re

with open('pratham_api.py', 'r', encoding='utf-16') as f:
    pratham_code = f.read()

with open('backend/app/api.py', 'r', encoding='utf-8') as f:
    main_code = f.read()

missing_imports = [
    'from app import services',
    'from fastapi import Request',
    'from app.models import *'
]

imports_block = '\n'.join(missing_imports)

routes_to_extract = ['/voice', '/dashboard', '/caregiver/elders', '/alerts', '/relationships', '/conversation', '/devices', '/notifications']

pratham_routes = []
blocks = re.split(r'\n@api_router\.', pratham_code)
for block in blocks[1:]:
    try:
        route = block.split('"')[1]
        if any(route.startswith(r) for r in routes_to_extract):
            pratham_routes.append('\n@router.' + block)
    except IndexError:
        pass

append_code = imports_block + '\n' + ''.join(pratham_routes)

with open('backend/app/api.py', 'a', encoding='utf-8') as f:
    f.write('\n\n# --- Merged from Pratham ---\n')
    f.write(append_code)
