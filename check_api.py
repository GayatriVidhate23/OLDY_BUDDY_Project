import re
with open('backend/app/api.py', 'r', encoding='utf-8') as f:
    api = f.read()

print('ElderProfile in register:', bool(re.search(r'db\.add\(ElderProfile\(', api)))
print('POST /elders exists:', bool(re.search(r'@router\.post\("/elders"', api)))

if 'pass # already handled' in api:
    print('Already handled is present')
