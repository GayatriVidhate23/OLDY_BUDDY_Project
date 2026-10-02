# Oldy Buddy Backend

Clean modular monolith backend for Oldy Buddy.

## Features
- Authentication & RBAC (Elder, Caregiver, Family, Admin)
- Elder Profiles & Activities
- Intelligence Architecture (Context, Intent, Policy, Workflow Engines)

## Setup
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
docker-compose up -d db redis
alembic upgrade head
uvicorn app.main:app --reload
```

## Testing
```bash
pytest
```
