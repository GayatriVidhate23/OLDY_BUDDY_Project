# Oldy Buddy Backend

FastAPI Backend Architecture for Oldy Buddy Elder Care Companion.

## Features
- JWT Authentication & Refresh Tokens
- Role-based Authorization (ELDER, CAREGIVER, FAMILY, ADMIN)
- Elder Profiles, Medical Info & User Relationships
- Activities, Reminders, Check-ins & Emergency SOS Alerts
- Voice Agent & Telephony Mocking
- Decision Engine & Multi-Channel Notifications (Module 6 Outbox Pattern)
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
