import glob
import os

for f in glob.glob('backend/tests/*.py'):
    with open(f, 'r', encoding='utf-8') as file:
        c = file.read()
    c = c.replace('"pass"', '"StrongPassword1!"')
    c = c.replace('"password"', '"StrongPassword1!"')
    with open(f, 'w', encoding='utf-8') as file:
        file.write(c)
