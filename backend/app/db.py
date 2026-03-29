"""SQLite helpers and schema initialization."""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

from app.config import settings


def ensure_runtime_directories() -> None:
    """Create required storage folders."""
    for path in (settings.data_dir, settings.storage_root, settings.upload_dir, settings.export_dir):
        Path(path).mkdir(parents=True, exist_ok=True)


@contextmanager
def get_connection() -> Iterator[sqlite3.Connection]:
    """Open a SQLite connection with row factory enabled."""
    ensure_runtime_directories()
    conn = sqlite3.connect(settings.database_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def json_dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


def json_loads(value: str | None, default: Any) -> Any:
    if not value:
        return default
    return json.loads(value)


def init_db() -> None:
    """Create application tables if they do not exist."""
    ensure_runtime_directories()
    with get_connection() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS projects (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                summary TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                active_requirement_version_id TEXT,
                active_design_version_id TEXT,
                active_build_version_id TEXT
            );

            CREATE TABLE IF NOT EXISTS uploaded_assets (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                filename TEXT NOT NULL,
                content_type TEXT NOT NULL,
                size_bytes INTEGER NOT NULL,
                storage_path TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS assistant_messages (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS requirement_versions (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                version_number INTEGER NOT NULL,
                status TEXT NOT NULL,
                provider TEXT NOT NULL,
                model TEXT NOT NULL,
                source_input_json TEXT NOT NULL,
                brief_json TEXT NOT NULL,
                approved INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                approved_at TEXT
            );

            CREATE TABLE IF NOT EXISTS design_versions (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                requirement_version_id TEXT NOT NULL,
                version_number INTEGER NOT NULL,
                status TEXT NOT NULL,
                provider TEXT NOT NULL,
                model TEXT NOT NULL,
                design_json TEXT NOT NULL,
                approved INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                approved_at TEXT
            );

            CREATE TABLE IF NOT EXISTS build_versions (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                design_version_id TEXT NOT NULL,
                version_number INTEGER NOT NULL,
                status TEXT NOT NULL,
                provider TEXT NOT NULL,
                model TEXT NOT NULL,
                manifest_json TEXT NOT NULL,
                export_root_path TEXT NOT NULL,
                export_zip_path TEXT NOT NULL,
                created_at TEXT NOT NULL,
                completed_at TEXT
            );

            CREATE TABLE IF NOT EXISTS generation_runs (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                stage TEXT NOT NULL,
                provider TEXT NOT NULL,
                model TEXT NOT NULL,
                prompt_version TEXT NOT NULL,
                status TEXT NOT NULL,
                latency_ms INTEGER NOT NULL DEFAULT 0,
                token_usage_json TEXT NOT NULL,
                error_message TEXT,
                output_ref_id TEXT,
                created_at TEXT NOT NULL,
                completed_at TEXT
            );
            """
        )
