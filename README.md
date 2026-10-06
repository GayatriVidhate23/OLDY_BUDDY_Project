# Oldy Buddy — Complete Elderly Care Platform

Oldy Buddy is an integrated elderly care companion platform powered by Python FastAPI, React Native (Expo), and React TypeScript.

---

## 🏗️ Platform Architecture

One Elder = One Source of Truth across 3 connected interfaces:

1. **Elderly Mobile App** (`frontend/`)
   - React Native + Expo + TypeScript
   - Simple, high-contrast, elderly-friendly UI with 6 core screens:
     - Login, Home, Reminders, AI Conversation, SOS Help, Profile

2. **AI Voice Agent & Telephony Integration** (`backend/app/api.py`)
   - Automated check-in call dispatching
   - Telephony webhooks (`/voice/webhook`) with STT -> AI -> TTS response pipeline
   - Call history logs & AI transcript summaries

3. **Family & Caregiver Web Dashboard** (`dashboard/`)
   - React + TypeScript + Vite web portal
   - Modern Navy + Lime SaaS design
   - Real-time elder health/SOS status, reminders manager, voice call logs & policy alert resolution

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
├── frontend/                 # Elderly Mobile App
│   ├── app/                  # Expo Router screens (Login, Home, Reminders, Conversation, SOS, Profile)
│   ├── components/           # High contrast UI elements (Card.tsx)
│   ├── services/             # API client (api.ts)
│   ├── store/                # Auth state store (authStore.ts)
│   ├── package.json
│   └── README.md
│
├── dashboard/                # Family & Caregiver Web Dashboard
│   ├── src/
│   │   ├── components/       # Dashboard components (ElderStatusCard, RemindersManager, VoiceCallHistory, AlertsFeed, ElderProfileView)
│   │   ├── api.ts            # Dashboard API integration
│   │   ├── App.tsx           # Dashboard main app
│   │   ├── index.css         # SaaS styling system
│   │   └── main.tsx
│   ├── package.json
│   ├── vite.config.ts
│   └── index.html
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

### 2. Run Elderly Mobile App
```bash
npm run frontend
# Launches Expo mobile app web preview
```

### 3. Run Family / Caregiver Dashboard
```bash
npm run dashboard
# Starts Caregiver Portal on http://localhost:3000
```

---

## 🧪 Running Tests

To run the backend test suite:
```bash
cd backend
python -m pytest
```
