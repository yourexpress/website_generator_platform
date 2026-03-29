# Website Generator Platform v1

Website Generator Platform is an admin-facing web application that turns rough inputs into:

- a polished requirement brief
- a structured UX/UI design specification
- a downloadable static website export bundle

The platform is built as a standalone repository with:

- `frontend/`: React + Vite operator interface
- `backend/`: FastAPI orchestration API, SQLite persistence, upload storage, and ZIP export generation
- `docs/`: product, architecture, API, data model, operator, and export specifications
- `docker-compose.yml`: two-container local or server deployment entrypoint

## Current implementation status

This repository includes a working scaffold for the full v1 workflow:

- simple admin cookie auth
- project creation and reopening
- asset uploads
- requirement refinement
- design generation
- static build generation
- ZIP download
- provider registry for OpenAI, Gemini, Claude, and DeepSeek
- metadata-only internet image suggestions

By default, generation runs in a deterministic offline fallback mode so the app works locally without API keys. The provider abstraction and server-managed model registry are already in place for future live API execution.

## Repository layout

```text
website_generator_platform/
  README.md
  docs/
    PRODUCT_REQUIREMENTS.md
    SYSTEM_ARCHITECTURE.md
    API_DESIGN.md
    DATA_MODEL.md
    SEQUENCE_DIAGRAMS.md
    EXPORT_BUNDLE_SPEC.md
    OPERATOR_SETUP.md
  backend/
    app/
    tests/
    .env.example
    requirements.txt
  frontend/
    src/
    package.json
```

## Quick start

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

Open `http://localhost:5173`.

Default local credentials are:

- username: `admin`
- password: `change-me`

Change them immediately in `backend/.env` for any non-local environment.

## Container deployment

The repository now supports a Docker deployment with:

- `frontend/`: built into an Nginx image
- `backend/`: packaged as a FastAPI/Uvicorn image
- `docker-compose.yml`: wiring for both containers plus persistent backend data/storage mounts

Quick start:

```bash
cd backend
cp .env.example .env
```

Set `CORS_ORIGINS=http://localhost:8080,http://127.0.0.1:8080`, then:

```bash
docker compose up --build
```

Open `http://localhost:8080`.

## Core product flow

1. Create a project.
2. Upload reference images.
3. Enter raw website requirements in Input Studio.
4. Generate a structured requirement brief.
5. Approve the brief.
6. Generate a design spec in Design Studio.
7. Approve the design.
8. Generate a static site build in Build Studio.
9. Download the ZIP export.

## Key constraints in v1

- static brochure-style websites only
- no CMS or dynamic application generation
- internet images are only suggested, never auto-downloaded
- uploaded assets are bundled into exports
- generation artifacts are versioned per stage

## Documentation index

- [Product requirements](docs/PRODUCT_REQUIREMENTS.md)
- [System architecture](docs/SYSTEM_ARCHITECTURE.md)
- [API design](docs/API_DESIGN.md)
- [Data model](docs/DATA_MODEL.md)
- [Sequence diagrams](docs/SEQUENCE_DIAGRAMS.md)
- [Export bundle specification](docs/EXPORT_BUNDLE_SPEC.md)
- [Operator setup guide](docs/OPERATOR_SETUP.md)
- [Container deployment](docs/CONTAINER_DEPLOYMENT.md)
