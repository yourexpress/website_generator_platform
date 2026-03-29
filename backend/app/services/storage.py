"""Filesystem storage helpers."""

from __future__ import annotations

import shutil
import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile, status

from app.config import settings


def project_upload_dir(project_id: str) -> Path:
    path = settings.upload_dir / project_id
    path.mkdir(parents=True, exist_ok=True)
    return path


def project_export_dir(project_id: str, build_id: str) -> Path:
    path = settings.export_dir / project_id / build_id
    path.mkdir(parents=True, exist_ok=True)
    return path


def save_upload(project_id: str, upload: UploadFile) -> tuple[str, int]:
    suffix = Path(upload.filename or "").suffix.lower()
    if suffix not in settings.allowed_upload_extensions:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported file type")
    target_dir = project_upload_dir(project_id)
    safe_name = f"{uuid.uuid4().hex[:10]}-{Path(upload.filename or 'upload').name}"
    target_path = target_dir / safe_name
    size = 0
    with target_path.open("wb") as handle:
        while True:
            chunk = upload.file.read(1024 * 1024)
            if not chunk:
                break
            size += len(chunk)
            if size > settings.max_upload_size_bytes:
                target_path.unlink(missing_ok=True)
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Upload exceeds size limit")
            handle.write(chunk)
    upload.file.close()
    return str(target_path), size


def copy_project_assets(asset_paths: list[str], destination_dir: Path) -> list[str]:
    assets_dir = destination_dir / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    copied: list[str] = []
    for source in asset_paths:
        source_path = Path(source)
        if not source_path.exists():
            continue
        target = assets_dir / source_path.name
        shutil.copy2(source_path, target)
        copied.append(f"assets/{target.name}")
    return copied
