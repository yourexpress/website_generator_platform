# System Architecture

## High-level structure

The platform has two deployable applications:

- `frontend/`: React + Vite operator interface
- `backend/`: FastAPI API with SQLite and filesystem-backed artifacts
- optional combined deployment via Docker Compose using separate frontend and backend containers

## Runtime components

### Frontend

- login screen for shared admin access
- project list and creation flow
- project workspace with three step modules:
  - Input Studio
  - Design Studio
  - Build Studio

### Backend

- auth router for session-based admin access
- project router for providers, projects, uploads, requirements, design, build, and download flows
- SQLite persistence for projects, versions, and run metadata
- filesystem storage for uploads and ZIP artifacts
- provider registry and adapter abstraction for:
  - OpenAI
  - Gemini
  - Claude
  - DeepSeek

## Generation architecture

The backend normalizes each provider behind the same interface:

- `refine_requirements(...)`
- `generate_design(...)`
- `generate_code(...)`

In the current scaffold, adapters use a deterministic template engine by default. This keeps local development and tests stable while preserving the final product shape for live LLM-backed generation.

## Persistence strategy

### SQLite

The following entities are stored in SQLite:

- `Project`
- `UploadedAsset`
- `RequirementVersion`
- `DesignVersion`
- `BuildVersion`
- `GenerationRun`

### Filesystem storage

- uploads: `backend/storage/uploads/<project_id>/`
- builds: `backend/storage/exports/<project_id>/<build_id>/`
- ZIP archives: `backend/storage/exports/<project_id>/<build_id>.zip`

## Security model

- shared admin username/password from environment variables
- signed session cookie for authenticated API access
- server-managed provider credentials only
- uploads restricted by file type and size

## Version flow

- multiple requirement versions per project
- one requirement version can be marked active
- multiple design versions per project
- one design version can be marked active
- multiple build versions per project
- one build version can be marked active

## Frontend to backend interaction

- all protected requests use cookie auth with `credentials: include`
- frontend polls project detail after mutations to refresh stage state
- ZIP downloads are direct backend file responses
