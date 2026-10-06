import glob
import re
import os

for f in glob.glob('backend/tests/*.py'):
    if os.path.isfile(f):
        with open(f, 'r', encoding='utf-8') as file:
            c = file.read()
        c = re.sub(r'"password"\s*:\s*"pass"', '"password": "StrongPassword1!"', c)
        c = re.sub(r'data=\{"username"\s*:\s*([^,]+),\s*"password"\s*:\s*"pass"\}', r'data={"username": \1, "password": "StrongPassword1!"}', c)
        with open(f, 'w', encoding='utf-8') as file:
            file.write(c)
