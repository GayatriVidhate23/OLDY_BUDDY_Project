# Oldy Buddy Backend

Minimal FastAPI MVP Backend for Oldy Buddy Elder Care Companion.

## Features
- JWT Authentication & Refresh Tokens
- Role-based Authorization (ELDER, CAREGIVER, FAMILY, ADMIN)
- Elder Profiles & Medical Info
- Activities, Reminders, Check-ins & Emergency SOS Alerts
- AI Assistant Conversation API
- Health Check Endpoint

## Quick Start
```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Running Tests
```bash
pytest
```
