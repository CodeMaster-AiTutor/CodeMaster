# CodeMaster Setup Guide (Current)

This guide reflects the current project setup, including Docker-based backend flow, local frontend, and local LLM service options.

## Setup Modes

- Recommended: Hybrid setup
  - Postgres + backend API in Docker
  - LLM service on host (local Python)
  - Frontend on host
- Optional: Full local setup (backend + frontend without Docker)

## Prerequisites

- Python 3.10+
- Node.js 18+
- Docker Desktop (required for recommended setup)
- Git

Verify:

```bash
python --version
node --version
npm --version
docker --version
docker compose version
```

## Project Structure

```text
CodeMaster/
├── backend/
├── frontend/
├── problems/
├── docker-compose.yml
└── SETUP_GUIDE.md
```

## 1) Environment Configuration

Create backend env file:

```bash
cd backend
copy env.example .env
```

Minimum required values in `backend/.env`:

```env
FLASK_APP=app
FLASK_ENV=development
SECRET_KEY=replace_me
JWT_SECRET_KEY=replace_me

USE_DOCKER=true
USE_EXTERNAL_LLM_SERVICE=true
LLM_SERVICE_URL=http://host.docker.internal:5002
LLM_SERVICE_TIMEOUT_SECONDS=90

AI_SERVICE=local_llm
AI_ERROR_FIX_SOURCE=local_llm
CODEMASTER_FORCE_GPU=0

CORS_ORIGINS=http://localhost:5173,http://localhost:8080
```

Frontend env (optional; default already points to backend API):

```bash
cd ..\frontend
echo VITE_API_BASE_URL=http://localhost:5001/api > .env
```

## 2) Recommended Run Flow (Hybrid Docker + Local LLM)

### Step A: Start local LLM service on host

From project root:

```bash
python backend/llm_service/app.py
```

Health check:

```bash
curl http://localhost:5002/health
```

### Step B: Start backend locally + postgres in Docker

Open a second terminal in project root:

```bash
docker compose up -d postgres
cd backend
python run.py
```

Backend health:

```bash
curl http://localhost:5001/api/health
```

### Step C: Seed database locally

```bash
cd backend
python seed_questions.py
python seed_content.py
```

### Step D: Run frontend

Open third terminal:

```bash
cd frontend
npm install
npm run dev
```

Open:

- Frontend: `http://localhost:5173`
- Backend API: `http://localhost:5001/api/health`

## 3) Full Local Setup

```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements-windows.txt
python flask_bootstrap.py
python seed_questions.py
python seed_content.py
python run.py
```

Then frontend:

```bash
cd ..\frontend
npm install
npm run dev
```

## 4) Data and Assessment Rules (Current)

- Assessment generation expects enough questions per level and type.
- Current selection behavior is random question sampling per assessment.
- Practice descriptions are loaded from:
  - `problems/Beginner Problems.txt`
  - `problems/Intemediate Problems.txt`
  - `problems/Advanced Problems.txt`
- Description import excludes:
  - `Test Cases`
  - `Test Scenarios`
  - `Test Results`

## 5) Daily Commands

From project root:

```bash
docker compose up -d postgres
python backend/llm_service/app.py
cd backend && python run.py
cd frontend && npm run dev
```

Stop services:

```bash
docker compose down
```

## 6) Troubleshooting

### “Insufficient mcq questions for advanced. Need 10, found 0”

Usually means questions are not seeded in the running local DB.

```bash
cd backend
python seed_questions.py
```

Then verify counts:

```bash
cd backend
python -c "from app import create_app; from app.models.assessment import Question; from collections import defaultdict; app=create_app(); 
with app.app_context():
 c=defaultdict(int)
 for q in Question.query.all(): c[(q.difficulty,q.question_type)] += 1
 print(dict(sorted(c.items())))"
```

### LLM endpoints fail

- Ensure host LLM service is running on `http://localhost:5002`
- Ensure backend env uses:
  - `USE_EXTERNAL_LLM_SERVICE=false` for in-process local RAG

### Backend can’t run Java execution

- Ensure docker socket mount exists in compose:
  - `/var/run/docker.sock:/var/run/docker.sock`
- Ensure backend env has `USE_DOCKER=true`

### Frontend cannot reach backend

- Confirm `VITE_API_BASE_URL=http://localhost:5001/api`
- Confirm backend health returns healthy:
  - `http://localhost:5001/api/health`

## 7) Validation Checklist

- Backend health: `GET /api/health` returns healthy
- LLM health: `GET http://localhost:5002/health` returns 200
- Assessment starts without insufficient question errors
- Practice descriptions appear without test-case blocks
- Frontend loads Dashboard, Practice, Analytics without API errors

---

If you change `backend/.env`, restart local backend process.
