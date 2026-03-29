# Container Deployment

## Deployment shape

The repository supports a two-container deployment:

- `frontend`: Nginx serving the built React application and reverse proxying backend routes
- `backend`: FastAPI application running under Uvicorn

## Ports

- frontend: `8080` on the host maps to container port `80`
- backend: `8000` on the host maps to container port `8000`

In normal operator use, the frontend container is the primary entrypoint:

- UI: `http://localhost:8080`
- backend health via frontend proxy: `http://localhost:8080/health`

## Required setup

1. Copy the backend environment template:

```bash
cd backend
cp .env.example .env
```

2. Update at least:

- `ADMIN_USERNAME`
- `ADMIN_PASSWORD`
- `SESSION_SECRET`
- `CORS_ORIGINS`

For Docker on localhost, set:

```env
CORS_ORIGINS=http://localhost:8080,http://127.0.0.1:8080
```

3. From the repository root:

```bash
docker compose up --build
```

## Volumes

The compose file mounts:

- `backend/data` to persist the SQLite database
- `backend/storage` to persist uploads and generated ZIP exports

## Frontend API routing

The frontend container uses Nginx to proxy these paths to the backend container:

- `/api/*`
- `/auth/*`
- `/health`

This keeps the operator UI and API on the same origin in container deployments.

## Production notes

- replace default admin credentials before deployment
- use a strong `SESSION_SECRET`
- back up both `backend/data` and `backend/storage`
- if you enable live provider calls, set the provider API keys in `backend/.env`
