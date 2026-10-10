# Oldy Buddy — Complete Elderly Care Platform

Oldy Buddy is an integrated elderly care companion platform powered by Python FastAPI, React Native (Expo), and React TypeScript.

---

## 🏗️ Platform Architecture

One Elder = One Source of Truth across 3 connected interfaces:

1. **Backend & AI Voice Agent (Modules 6, 7, 8)** (`backend/`)
   - **Status**: Work in Progress (Pending Voice Agent)
   - Telephone integration, voice agent, notification, trends, messaging, and status.
   - Automated check-in call dispatching
   - Telephony webhooks (`/voice/webhook`) with STT -> AI -> TTS response pipeline
   - Call history logs & AI transcript summaries

---

## 📁 Repository Structure

```
OLDY_BUDDY_Project/
│
├── backend/                  # FastAPI Backend API & Database
│   ├── app/
│   │   ├── main.py           # Application startup & middleware
│   │   ├── database.py       # Async SQLAlchemy database & settings
│   │   ├── models.py         # DB Models (User, ElderProfile, Activity, VoiceCall, AlertNotification)
│   │   ├── schemas.py        # Pydantic validation schemas
│   │   ├── auth.py           # JWT Authentication & RBAC security
│   │   ├── services.py       # Core business logic & Policy Engine
│   │   └── api.py            # API routes
│   ├── tests/                # Async pytest test suite (6/6 passing)
│   ├── requirements.txt      # Python dependencies
│   └── README.md
│
├── package.json              # Root CLI helper scripts
└── README.md
```

---

## ⚡ Quick Start

### 1. Run Backend API
```bash
npm run backend
# Starts FastAPI server on http://127.0.0.1:8000 (Swagger docs at /docs)
```

---

## 🧪 Running Tests

To run the backend test suite:
```bash
cd backend
python -m pytest
```
