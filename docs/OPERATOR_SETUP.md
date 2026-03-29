# Operator Setup Guide

## Local setup

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
echo "VITE_API_BASE_URL=http://localhost:8000" > .env
npm run dev
```

## Environment configuration

Change these immediately:

- `ADMIN_USERNAME`
- `ADMIN_PASSWORD`
- `SESSION_SECRET`

Configure these when live provider execution is enabled:

- `OPENAI_API_KEY`
- `GEMINI_API_KEY`
- `CLAUDE_API_KEY`
- `DEEPSEEK_API_KEY`

If you want the current scaffold to remain deterministic and offline-friendly:

- leave `REAL_PROVIDER_CALLS_ENABLED=false`

## Operating workflow

1. Create a project.
2. Upload any images you want included in the export.
3. Fill the Input Studio form and run requirement polishing.
4. Approve the brief you want to drive design.
5. Generate and approve a design version.
6. Generate a build version.
7. Download the ZIP.

## Testing

```bash
cd backend
pip install -r requirements-dev.txt
pytest
```

## Storage notes

- SQLite database lives under `backend/data/`
- uploads live under `backend/storage/uploads/`
- build outputs and ZIPs live under `backend/storage/exports/`

Back up both the database and storage directories together.

## Container setup

For a two-container deployment using Docker, see [CONTAINER_DEPLOYMENT.md](CONTAINER_DEPLOYMENT.md).
