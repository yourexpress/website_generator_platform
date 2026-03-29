"""Persistence helpers for projects, versions, assets, and generation runs."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import HTTPException, status

from app.db import get_connection, json_dumps, json_loads
from app.schemas import BuildManifest, DesignSpec, RequirementBrief, RequirementInput


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def _count_versions(table: str, project_id: str) -> int:
    with get_connection() as conn:
        row = conn.execute(
            f"SELECT COUNT(*) AS count FROM {table} WHERE project_id = ?",
            (project_id,),
        ).fetchone()
        return int(row["count"])


def _project_exists(project_id: str) -> None:
    with get_connection() as conn:
        row = conn.execute("SELECT id FROM projects WHERE id = ?", (project_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")


def create_project(name: str, summary: str | None) -> dict[str, Any]:
    project_id = _new_id("proj")
    timestamp = _now()
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO projects (
                id, name, summary, created_at, updated_at,
                active_requirement_version_id, active_design_version_id, active_build_version_id
            ) VALUES (?, ?, ?, ?, ?, NULL, NULL, NULL)
            """,
            (project_id, name, summary, timestamp, timestamp),
        )
    return get_project(project_id)


def list_projects() -> list[dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT *
            FROM projects
            ORDER BY updated_at DESC, created_at DESC
            """
        ).fetchall()
    return [dict(row) for row in rows]


def get_project(project_id: str) -> dict[str, Any]:
    with get_connection() as conn:
        project = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
        if not project:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
        assets = conn.execute(
            "SELECT * FROM uploaded_assets WHERE project_id = ? ORDER BY created_at DESC",
            (project_id,),
        ).fetchall()
        requirement_versions = conn.execute(
            "SELECT * FROM requirement_versions WHERE project_id = ? ORDER BY version_number DESC",
            (project_id,),
        ).fetchall()
        design_versions = conn.execute(
            "SELECT * FROM design_versions WHERE project_id = ? ORDER BY version_number DESC",
            (project_id,),
        ).fetchall()
        build_versions = conn.execute(
            "SELECT * FROM build_versions WHERE project_id = ? ORDER BY version_number DESC",
            (project_id,),
        ).fetchall()
        generation_runs = conn.execute(
            "SELECT * FROM generation_runs WHERE project_id = ? ORDER BY created_at DESC",
            (project_id,),
        ).fetchall()
    return {
        **dict(project),
        "assets": [dict(row) for row in assets],
        "requirement_versions": [dict(row) for row in requirement_versions],
        "design_versions": [dict(row) for row in design_versions],
        "build_versions": [dict(row) for row in build_versions],
        "generation_runs": [dict(row) for row in generation_runs],
    }


def touch_project(project_id: str, **updates: Any) -> None:
    _project_exists(project_id)
    columns = ["updated_at = ?"]
    values: list[Any] = [_now()]
    for key, value in updates.items():
        columns.append(f"{key} = ?")
        values.append(value)
    values.append(project_id)
    with get_connection() as conn:
        conn.execute(
            f"UPDATE projects SET {', '.join(columns)} WHERE id = ?",
            tuple(values),
        )


def create_generation_run(project_id: str, stage: str, provider: str, model: str, prompt_version: str) -> dict[str, Any]:
    _project_exists(project_id)
    run_id = _new_id("run")
    timestamp = _now()
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO generation_runs (
                id, project_id, stage, provider, model, prompt_version, status,
                latency_ms, token_usage_json, error_message, output_ref_id, created_at, completed_at
            ) VALUES (?, ?, ?, ?, ?, ?, 'running', 0, '{}', NULL, NULL, ?, NULL)
            """,
            (run_id, project_id, stage, provider, model, prompt_version, timestamp),
        )
    return {"id": run_id, "created_at": timestamp}


def complete_generation_run(
    run_id: str,
    *,
    latency_ms: int,
    token_usage: dict[str, int],
    output_ref_id: str | None,
    error_message: str | None = None,
) -> None:
    status_value = "failed" if error_message else "completed"
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE generation_runs
            SET status = ?, latency_ms = ?, token_usage_json = ?, output_ref_id = ?,
                error_message = ?, completed_at = ?
            WHERE id = ?
            """,
            (
                status_value,
                latency_ms,
                json_dumps(token_usage),
                output_ref_id,
                error_message,
                _now(),
                run_id,
            ),
        )


def create_uploaded_asset(
    project_id: str,
    *,
    filename: str,
    content_type: str,
    size_bytes: int,
    storage_path: str,
) -> dict[str, Any]:
    _project_exists(project_id)
    asset_id = _new_id("asset")
    timestamp = _now()
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO uploaded_assets (id, project_id, filename, content_type, size_bytes, storage_path, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (asset_id, project_id, filename, content_type, size_bytes, storage_path, timestamp),
        )
    touch_project(project_id)
    return {
        "id": asset_id,
        "filename": filename,
        "content_type": content_type,
        "size_bytes": size_bytes,
        "storage_path": storage_path,
        "created_at": timestamp,
    }


def get_assets(project_id: str) -> list[dict[str, Any]]:
    _project_exists(project_id)
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM uploaded_assets WHERE project_id = ? ORDER BY created_at ASC",
            (project_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def create_requirement_version(
    project_id: str,
    *,
    provider: str,
    model: str,
    source_input: RequirementInput,
    brief: RequirementBrief,
) -> dict[str, Any]:
    version_id = _new_id("req")
    version_number = _count_versions("requirement_versions", project_id) + 1
    timestamp = _now()
    record = {
        "id": version_id,
        "version_number": version_number,
        "status": "completed",
        "approved": 0,
        "provider": provider,
        "model": model,
        "created_at": timestamp,
        "approved_at": None,
        "source_input_json": json_dumps(source_input.model_dump()),
        "brief_json": json_dumps(brief.model_dump()),
    }
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO requirement_versions (
                id, project_id, version_number, status, provider, model,
                source_input_json, brief_json, approved, created_at, approved_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, ?, NULL)
            """,
            (
                version_id,
                project_id,
                version_number,
                "completed",
                provider,
                model,
                record["source_input_json"],
                record["brief_json"],
                timestamp,
            ),
        )
    touch_project(project_id)
    return {
        **record,
        "source_input": source_input.model_dump(),
        "brief": brief.model_dump(),
    }


def approve_requirement_version(project_id: str, requirement_version_id: str) -> None:
    _project_exists(project_id)
    timestamp = _now()
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE requirement_versions
            SET approved = CASE WHEN id = ? THEN 1 ELSE 0 END,
                approved_at = CASE WHEN id = ? THEN ? ELSE approved_at END
            WHERE project_id = ?
            """,
            (requirement_version_id, requirement_version_id, timestamp, project_id),
        )
    touch_project(project_id, active_requirement_version_id=requirement_version_id)


def get_requirement_version(project_id: str, version_id: str | None) -> dict[str, Any]:
    _project_exists(project_id)
    query = "SELECT * FROM requirement_versions WHERE project_id = ?"
    params: list[Any] = [project_id]
    if version_id:
        query += " AND id = ?"
        params.append(version_id)
    else:
        query += " ORDER BY approved DESC, version_number DESC LIMIT 1"
    with get_connection() as conn:
        row = conn.execute(query, tuple(params)).fetchone()
    if not row:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Requirement version unavailable")
    data = dict(row)
    data["source_input"] = json_loads(data.pop("source_input_json"), {})
    data["brief"] = json_loads(data.pop("brief_json"), {})
    return data


def create_design_version(
    project_id: str,
    *,
    requirement_version_id: str,
    provider: str,
    model: str,
    design: DesignSpec,
) -> dict[str, Any]:
    version_id = _new_id("design")
    version_number = _count_versions("design_versions", project_id) + 1
    timestamp = _now()
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO design_versions (
                id, project_id, requirement_version_id, version_number, status,
                provider, model, design_json, approved, created_at, approved_at
            ) VALUES (?, ?, ?, ?, 'completed', ?, ?, ?, 0, ?, NULL)
            """,
            (
                version_id,
                project_id,
                requirement_version_id,
                version_number,
                provider,
                model,
                json_dumps(design.model_dump()),
                timestamp,
            ),
        )
    touch_project(project_id)
    return {
        "id": version_id,
        "requirement_version_id": requirement_version_id,
        "version_number": version_number,
        "status": "completed",
        "approved": 0,
        "provider": provider,
        "model": model,
        "created_at": timestamp,
        "approved_at": None,
        "design": design.model_dump(),
    }


def approve_design_version(project_id: str, design_version_id: str) -> None:
    _project_exists(project_id)
    timestamp = _now()
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE design_versions
            SET approved = CASE WHEN id = ? THEN 1 ELSE 0 END,
                approved_at = CASE WHEN id = ? THEN ? ELSE approved_at END
            WHERE project_id = ?
            """,
            (design_version_id, design_version_id, timestamp, project_id),
        )
    touch_project(project_id, active_design_version_id=design_version_id)


def get_design_version(project_id: str, version_id: str | None) -> dict[str, Any]:
    _project_exists(project_id)
    query = "SELECT * FROM design_versions WHERE project_id = ?"
    params: list[Any] = [project_id]
    if version_id:
        query += " AND id = ?"
        params.append(version_id)
    else:
        query += " ORDER BY approved DESC, version_number DESC LIMIT 1"
    with get_connection() as conn:
        row = conn.execute(query, tuple(params)).fetchone()
    if not row:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Design version unavailable")
    data = dict(row)
    data["design"] = json_loads(data.pop("design_json"), {})
    return data


def create_build_version(
    project_id: str,
    *,
    design_version_id: str,
    provider: str,
    model: str,
    manifest: BuildManifest,
    export_root_path: str,
    export_zip_path: str,
) -> dict[str, Any]:
    version_id = manifest.build_id
    version_number = _count_versions("build_versions", project_id) + 1
    timestamp = _now()
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO build_versions (
                id, project_id, design_version_id, version_number, status,
                provider, model, manifest_json, export_root_path, export_zip_path,
                created_at, completed_at
            ) VALUES (?, ?, ?, ?, 'completed', ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                version_id,
                project_id,
                design_version_id,
                version_number,
                provider,
                model,
                json_dumps(manifest.model_dump(mode="json")),
                export_root_path,
                export_zip_path,
                timestamp,
                timestamp,
            ),
        )
    touch_project(project_id, active_build_version_id=version_id)
    return {
        "id": version_id,
        "design_version_id": design_version_id,
        "version_number": version_number,
        "status": "completed",
        "provider": provider,
        "model": model,
        "created_at": timestamp,
        "completed_at": timestamp,
        "manifest": manifest.model_dump(mode="json"),
        "export_root_path": export_root_path,
        "export_zip_path": export_zip_path,
    }


def get_build_version(project_id: str, build_id: str) -> dict[str, Any]:
    _project_exists(project_id)
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM build_versions WHERE project_id = ? AND id = ?",
            (project_id, build_id),
        ).fetchone()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Build version not found")
    data = dict(row)
    data["manifest"] = json_loads(data.pop("manifest_json"), {})
    return data
