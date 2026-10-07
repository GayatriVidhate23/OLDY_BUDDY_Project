# Oldy Buddy — Complete Elderly Care Platform (Backend)

Oldy Buddy is an integrated elderly care companion platform. This repository contains the **unified, fully-tested backend API** built with Python FastAPI and SQLite/PostgreSQL.

---

## 🚀 Completed Backend Modules

The backend architecture is broken down into interconnected, highly-tested modules:

- **M0 — Foundation:** Async SQLAlchemy configuration, Pydantic data schemas, and structured logging.
- **M1 — Authentication:** Robust JWT-based authentication, password policies, token refreshing, OTP infrastructure, and Role-Based Access Control (RBAC) for `ELDER`, `CAREGIVER`, and `ADMIN`.
- **M2 — User Data:** Elder profile management, multi-language preferences, and Caregiver-Elder relationship linking.
- **M3 — Intelligence:** LLM-agnostic classifier pipeline, fallback providers (Sarvam AI / Fake), and strict semantic guardrails preventing medical advice and blocking unhandled intent regressions.
- **M4 — Reminders:** Scheduling and managing recurring check-ins and medication reminders.
- **M5 — Events & Decision Engine:** Dynamic rule-based decision engine triggering actions, evaluating SOS protocols, and assessing check-in compliance.
- **M6 — Notifications:** Multi-channel alerting (Push, SMS, Webhook) with escalation policies, fallback mechanisms, and guaranteed transactional dispatch.
- **M7 — Telephony & Voice Agent:** Outbound check-in calls, Voice Webhook (`/voice/outbound`), and STT -> AI -> TTS synthesis loops.

---

## 📂 Repository Structure

```
OLDY_BUDDY_Project/
│
├── backend/                  # FastAPI Backend API & Database
│   ├── alembic/              # Database migration configurations
│   ├── app/
│   │   ├── intelligence/     # LLM providers, guardrails, & classifiers
│   │   ├── services/         # Core business logic & Notification dispatch
│   │   ├── models/           # SQLAlchemy DB Models
│   │   ├── main.py           # Application startup & middleware
│   │   ├── database.py       # Async SQLAlchemy database & settings
│   │   ├── schemas.py        # Pydantic validation schemas
│   │   ├── auth.py           # JWT Authentication & RBAC security
│   │   ├── decision_engine.py# Event evaluation logic
│   │   └── api.py            # API routing handlers
│   │
│   ├── tests/                # Comprehensive Async Pytest suite (330+ passing tests)
│   ├── requirements.txt      # Python dependencies
│   └── seed_data.py          # Development database seeder
│
└── README.md
```

---

## 🛠️ Quick Start

### 1. Setup Environment
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Copy the required configuration. You will need a secure JWT secret:
```bash
# Windows PowerShell
$env:JWT_SECRET_KEY="your-secure-secret-key-here"
```

### 3. Run Database Migrations
```bash
alembic upgrade head
```

### 4. Run Backend API
```bash
uvicorn app.main:app --reload
# Starts FastAPI server on http://127.0.0.1:8000
# Interactive Swagger docs available at http://127.0.0.1:8000/docs
```

---

## 🧪 Running Tests

The repository contains an exhaustive test suite covering integration, intelligence guardrails, notifications, and auth flows.

```bash
cd backend
$env:JWT_SECRET_KEY="oldy-buddy-test-secret-key-2026-very-long-random-value"
python -m pytest -v
```
