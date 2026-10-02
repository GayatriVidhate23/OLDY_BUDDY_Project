import os

base_dir = r"c:\Users\gayat\Documents\OLDY_BUDDY_Project\backend"

directories = [
    "app/core",
    "app/db",
    "app/models",
    "app/schemas",
    "app/api/v1/endpoints",
    "app/services",
    "app/repositories",
    "app/intelligence",
    "app/workers",
    "app/tests/api/v1",
    "app/tests/services",
    "alembic/versions"
]

for d in directories:
    os.makedirs(os.path.join(base_dir, d), exist_ok=True)

# Also create __init__.py files
for root, dirs, files in os.walk(os.path.join(base_dir, "app")):
    with open(os.path.join(root, "__init__.py"), "w") as f:
        pass
with open(os.path.join(base_dir, "app/tests/__init__.py"), "w") as f:
    pass

print("Directories and __init__.py created.")
