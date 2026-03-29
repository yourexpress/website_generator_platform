# API Design

## Authentication

### `POST /auth/login`

Request:

```json
{
  "username": "admin",
  "password": "change-me"
}
```

Behavior:

- validates shared admin credentials
- sets signed session cookie

### `POST /auth/logout`

Behavior:

- clears session cookie

## Protected endpoints

All `/api/*` routes require the admin session cookie.

### `GET /api/providers`

Returns provider catalog entries with:

- provider name
- whether credentials are configured
- whether offline fallback is available
- default models by stage

### `GET /api/projects`

Returns project summaries.

### `POST /api/projects`

Creates a project.

Request:

```json
{
  "name": "Northwind Studio",
  "summary": "Creative agency brochure site"
}
```

### `GET /api/projects/{project_id}`

Returns full project detail including:

- assets
- requirement versions
- design versions
- build versions
- generation runs

### `POST /api/projects/{project_id}/uploads`

Multipart form upload.

Form fields:

- `files`: one or more image files

### `POST /api/projects/{project_id}/requirements/refine`

Creates a new requirement version from raw input.

### `POST /api/projects/{project_id}/requirements/approve`

Query param:

- `requirement_version_id`

Marks the selected requirement version as active and approved.

### `POST /api/projects/{project_id}/design/generate`

Request fields:

- provider/model selection
- optional `requirement_version_id`

Creates a new design version.

### `POST /api/projects/{project_id}/design/approve`

Query param:

- `design_version_id`

Marks the selected design version as active and approved.

### `POST /api/projects/{project_id}/build/generate`

Request fields:

- provider/model selection
- optional `design_version_id`

Creates a new static build version and ZIP export.

### `GET /api/projects/{project_id}/builds/{build_id}`

Returns manifest metadata and filesystem paths for the selected build version.

### `GET /api/projects/{project_id}/builds/{build_id}/download`

Returns the generated ZIP file.

### `GET /api/projects/{project_id}/image-suggestions`

Returns metadata-only licensed source suggestions derived from the current requirement brief.

## Health

### `GET /health`

Simple health check.
