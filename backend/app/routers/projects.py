"""Project and generation API endpoints."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, File, UploadFile
from fastapi.responses import FileResponse

from app.auth import AdminSession
from app.config import settings
from app.schemas import (
    AssistantChatRequest,
    AssistantChatResponse,
    AssistantMessage,
    ApproveVersionResponse,
    BuildVersionOut,
    DesignSpec,
    DesignVersionOut,
    GenerateBuildRequest,
    GenerateDesignRequest,
    ImageSuggestionsResponse,
    ProjectCreateRequest,
    ProjectDetail,
    ProjectSummary,
    ProviderCatalogResponse,
    RefineRequirementsRequest,
    RequirementBrief,
    RequirementInput,
    RequirementVersionOut,
    UploadedAssetOut,
)
from app.services.export_service import generate_static_export
from app.services.image_suggestions import build_image_suggestions
from app.services.project_store import (
    approve_design_version,
    approve_requirement_version,
    complete_generation_run,
    create_assistant_message,
    create_build_version,
    create_generation_run,
    create_project,
    create_requirement_version,
    create_design_version,
    create_uploaded_asset,
    get_assets,
    get_build_version,
    get_design_version,
    get_project,
    get_requirement_version,
    list_assistant_messages,
    list_projects,
    touch_project,
)
from app.services.provider_registry import provider_registry
from app.services.providers import template_engine
from app.services.storage import save_upload


router = APIRouter(prefix="/api", tags=["projects"], dependencies=[AdminSession])


def _to_datetime(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value) if value else None


def _project_summary(record: dict[str, Any]) -> ProjectSummary:
    return ProjectSummary(
        id=record["id"],
        name=record["name"],
        summary=record["summary"],
        created_at=datetime.fromisoformat(record["created_at"]),
        updated_at=datetime.fromisoformat(record["updated_at"]),
        active_requirement_version_id=record["active_requirement_version_id"],
        active_design_version_id=record["active_design_version_id"],
        active_build_version_id=record["active_build_version_id"],
    )


def _asset_out(record: dict[str, Any]) -> UploadedAssetOut:
    return UploadedAssetOut(
        id=record["id"],
        filename=record["filename"],
        content_type=record["content_type"],
        size_bytes=record["size_bytes"],
        storage_path=record["storage_path"],
        created_at=datetime.fromisoformat(record["created_at"]),
    )


def _assistant_message_out(record: dict[str, Any]) -> AssistantMessage:
    return AssistantMessage(
        id=record["id"],
        role=record["role"],
        content=record["content"],
        created_at=datetime.fromisoformat(record["created_at"]),
    )


def _requirement_out(record: dict[str, Any]) -> RequirementVersionOut:
    return RequirementVersionOut(
        id=record["id"],
        version_number=record["version_number"],
        status=record["status"],
        approved=bool(record["approved"]),
        provider=record["provider"],
        model=record["model"],
        created_at=datetime.fromisoformat(record["created_at"]),
        approved_at=_to_datetime(record.get("approved_at")),
        source_input=record["source_input"],
        brief=RequirementBrief.model_validate(record["brief"]),
    )


def _design_out(record: dict[str, Any]) -> DesignVersionOut:
    return DesignVersionOut(
        id=record["id"],
        requirement_version_id=record["requirement_version_id"],
        version_number=record["version_number"],
        status=record["status"],
        approved=bool(record["approved"]),
        provider=record["provider"],
        model=record["model"],
        created_at=datetime.fromisoformat(record["created_at"]),
        approved_at=_to_datetime(record.get("approved_at")),
        design=DesignSpec.model_validate(record["design"]),
    )


def _build_out(record: dict[str, Any]) -> BuildVersionOut:
    from app.schemas import BuildManifest

    return BuildVersionOut(
        id=record["id"],
        design_version_id=record["design_version_id"],
        version_number=record["version_number"],
        status=record["status"],
        provider=record["provider"],
        model=record["model"],
        created_at=datetime.fromisoformat(record["created_at"]),
        completed_at=_to_datetime(record.get("completed_at")),
        manifest=BuildManifest.model_validate(record["manifest"]),
        export_root_path=record["export_root_path"],
        export_zip_path=record["export_zip_path"],
    )


def _project_detail(record: dict[str, Any]) -> ProjectDetail:
    return ProjectDetail(
        **_project_summary(record).model_dump(),
        assets=[_asset_out(item) for item in record["assets"]],
        assistant_messages=[_assistant_message_out(item) for item in record["assistant_messages"]],
        requirement_versions=[_requirement_out(_normalize_requirement_record(item)) for item in record["requirement_versions"]],
        design_versions=[_design_out(_normalize_design_record(item)) for item in record["design_versions"]],
        build_versions=[_build_out(_normalize_build_record(item)) for item in record["build_versions"]],
        generation_runs=[_generation_run_out(item) for item in record["generation_runs"]],
    )


def _normalize_requirement_record(item: dict[str, Any]) -> dict[str, Any]:
    if "source_input" in item:
        return item
    from app.db import json_loads

    item = dict(item)
    item["source_input"] = json_loads(item.pop("source_input_json"), {})
    item["brief"] = json_loads(item.pop("brief_json"), {})
    return item


def _normalize_design_record(item: dict[str, Any]) -> dict[str, Any]:
    if "design" in item:
        return item
    from app.db import json_loads

    item = dict(item)
    item["design"] = json_loads(item.pop("design_json"), {})
    return item


def _normalize_build_record(item: dict[str, Any]) -> dict[str, Any]:
    if "manifest" in item:
        return item
    from app.db import json_loads

    item = dict(item)
    item["manifest"] = json_loads(item.pop("manifest_json"), {})
    return item


def _generation_run_out(item: dict[str, Any]):
    from app.db import json_loads
    from app.schemas import GenerationRunSummary

    return GenerationRunSummary(
        id=item["id"],
        stage=item["stage"],
        provider=item["provider"],
        model=item["model"],
        prompt_version=item["prompt_version"],
        status=item["status"],
        latency_ms=item["latency_ms"],
        token_usage=json_loads(item["token_usage_json"], {}),
        error_message=item["error_message"],
        output_ref_id=item["output_ref_id"],
        created_at=datetime.fromisoformat(item["created_at"]),
        completed_at=_to_datetime(item["completed_at"]),
    )


@router.get("/providers", response_model=ProviderCatalogResponse)
async def get_provider_catalog() -> ProviderCatalogResponse:
    return ProviderCatalogResponse(providers=provider_registry.catalog())


@router.get("/projects", response_model=list[ProjectSummary])
async def get_projects() -> list[ProjectSummary]:
    return [_project_summary(item) for item in list_projects()]


@router.post("/projects", response_model=ProjectSummary)
async def create_project_endpoint(payload: ProjectCreateRequest) -> ProjectSummary:
    return _project_summary(create_project(payload.name, payload.summary))


@router.get("/projects/{project_id}", response_model=ProjectDetail)
async def get_project_endpoint(project_id: str) -> ProjectDetail:
    return _project_detail(get_project(project_id))


@router.post("/projects/{project_id}/uploads", response_model=list[UploadedAssetOut])
async def upload_assets(project_id: str, files: list[UploadFile] = File(...)) -> list[UploadedAssetOut]:
    saved_assets: list[UploadedAssetOut] = []
    for upload in files:
        storage_path, size = save_upload(project_id, upload)
        record = create_uploaded_asset(
            project_id,
            filename=upload.filename or Path(storage_path).name,
            content_type=upload.content_type or "application/octet-stream",
            size_bytes=size,
            storage_path=storage_path,
        )
        saved_assets.append(_asset_out(record))
    return saved_assets


@router.post("/projects/{project_id}/assistant/chat", response_model=AssistantChatResponse)
async def chat_with_assistant(project_id: str, payload: AssistantChatRequest) -> AssistantChatResponse:
    project = get_project(project_id)
    assets = get_assets(project_id)
    previous_requirement = _normalize_requirement_record(project["requirement_versions"][0]) if project["requirement_versions"] else None
    user_message = create_assistant_message(project_id, role="user", content=payload.message)
    conversation = list_assistant_messages(project_id)
    user_messages = [item["content"] for item in conversation if item["role"] == "user"]
    requirement_input = template_engine.build_requirement_input_from_conversation(
        project_name=project["name"],
        project_summary=project["summary"],
        messages=user_messages,
        site_type=payload.site_type,
        preferred_page_count=payload.preferred_page_count,
        uploaded_asset_ids=payload.uploaded_asset_ids,
        previous_input=(
            RequirementInput.model_validate(previous_requirement["source_input"])
            if previous_requirement
            else None
        ),
    )

    selected_assets = [item["filename"] for item in assets if item["id"] in payload.uploaded_asset_ids] or [item["filename"] for item in assets]
    provider = provider_registry.get(payload.selection.provider)

    requirements_model = payload.selection.model or provider.default_model("requirements")
    requirements_run = create_generation_run(
        project_id,
        "requirements",
        payload.selection.provider,
        requirements_model,
        settings.prompt_template_version,
    )
    requirement_result = await provider.refine_requirements(
        project_name=project["name"],
        payload=requirement_input,
        asset_filenames=selected_assets,
        model=requirements_model,
    )
    requirement_record = create_requirement_version(
        project_id,
        provider=payload.selection.provider,
        model=requirements_model,
        source_input=requirement_input,
        brief=requirement_result.output,
    )
    complete_generation_run(
        requirements_run["id"],
        latency_ms=requirement_result.latency_ms,
        token_usage=requirement_result.token_usage,
        output_ref_id=requirement_record["id"],
    )

    design_model = payload.selection.model or provider.default_model("design")
    design_run = create_generation_run(
        project_id,
        "design",
        payload.selection.provider,
        design_model,
        settings.prompt_template_version,
    )
    design_result = await provider.generate_design(
        brief=RequirementBrief.model_validate(requirement_record["brief"]),
        asset_filenames=selected_assets,
        model=design_model,
    )
    design_record = create_design_version(
        project_id,
        requirement_version_id=requirement_record["id"],
        provider=payload.selection.provider,
        model=design_model,
        design=design_result.output,
    )
    complete_generation_run(
        design_run["id"],
        latency_ms=design_result.latency_ms,
        token_usage=design_result.token_usage,
        output_ref_id=design_record["id"],
    )
    touch_project(
        project_id,
        active_requirement_version_id=requirement_record["id"],
        active_design_version_id=design_record["id"],
    )

    assistant_text = template_engine.build_assistant_reply(
        brief=RequirementBrief.model_validate(requirement_record["brief"]),
        design=DesignSpec.model_validate(design_record["design"]),
        message_count=len(user_messages),
    )
    assistant_message = create_assistant_message(project_id, role="assistant", content=assistant_text)
    return AssistantChatResponse(
        user_message=_assistant_message_out(user_message),
        assistant_message=_assistant_message_out(assistant_message),
        requirement_version=_requirement_out(requirement_record),
        design_version=_design_out(design_record),
    )


@router.post("/projects/{project_id}/requirements/refine", response_model=RequirementVersionOut)
async def refine_requirements(project_id: str, payload: RefineRequirementsRequest) -> RequirementVersionOut:
    project = get_project(project_id)
    assets = get_assets(project_id)
    asset_filenames = [item["filename"] for item in assets if item["id"] in payload.input.uploaded_asset_ids] or [
        item["filename"] for item in assets
    ]
    provider = provider_registry.get(payload.selection.provider)
    model = payload.selection.model or provider.default_model("requirements")
    run = create_generation_run(project_id, "requirements", payload.selection.provider, model, settings.prompt_template_version)
    result = await provider.refine_requirements(
        project_name=project["name"],
        payload=payload.input,
        asset_filenames=asset_filenames,
        model=model,
    )
    record = create_requirement_version(
        project_id,
        provider=payload.selection.provider,
        model=model,
        source_input=payload.input,
        brief=result.output,
    )
    complete_generation_run(
        run["id"],
        latency_ms=result.latency_ms,
        token_usage=result.token_usage,
        output_ref_id=record["id"],
    )
    return _requirement_out(record)


@router.post("/projects/{project_id}/requirements/approve", response_model=ApproveVersionResponse)
async def approve_requirements(project_id: str, requirement_version_id: str) -> ApproveVersionResponse:
    approve_requirement_version(project_id, requirement_version_id)
    return ApproveVersionResponse(ok=True, project_id=project_id, approved_version_id=requirement_version_id)


@router.post("/projects/{project_id}/design/generate", response_model=DesignVersionOut)
async def generate_design(project_id: str, payload: GenerateDesignRequest) -> DesignVersionOut:
    requirement = get_requirement_version(project_id, payload.requirement_version_id)
    assets = get_assets(project_id)
    provider = provider_registry.get(payload.selection.provider)
    model = payload.selection.model or provider.default_model("design")
    run = create_generation_run(project_id, "design", payload.selection.provider, model, settings.prompt_template_version)
    result = await provider.generate_design(
        brief=RequirementBrief.model_validate(requirement["brief"]),
        asset_filenames=[item["filename"] for item in assets],
        model=model,
    )
    record = create_design_version(
        project_id,
        requirement_version_id=requirement["id"],
        provider=payload.selection.provider,
        model=model,
        design=result.output,
    )
    complete_generation_run(
        run["id"],
        latency_ms=result.latency_ms,
        token_usage=result.token_usage,
        output_ref_id=record["id"],
    )
    return _design_out(record)


@router.post("/projects/{project_id}/design/approve", response_model=ApproveVersionResponse)
async def approve_design(project_id: str, design_version_id: str) -> ApproveVersionResponse:
    approve_design_version(project_id, design_version_id)
    return ApproveVersionResponse(ok=True, project_id=project_id, approved_version_id=design_version_id)


@router.post("/projects/{project_id}/build/generate", response_model=BuildVersionOut)
async def generate_build(project_id: str, payload: GenerateBuildRequest) -> BuildVersionOut:
    design_record = get_design_version(project_id, payload.design_version_id)
    design = DesignSpec.model_validate(design_record["design"])
    assets = get_assets(project_id)
    provider = provider_registry.get(payload.selection.provider)
    model = payload.selection.model or provider.default_model("build")
    run = create_generation_run(project_id, "build", payload.selection.provider, model, settings.prompt_template_version)
    result = await provider.generate_code(
        design=design,
        asset_filenames=[item["filename"] for item in assets],
        model=model,
    )
    manifest, export_root_path, export_zip_path = generate_static_export(
        project_id,
        design,
        provider=payload.selection.provider,
        model=model,
        asset_paths=[item["storage_path"] for item in assets],
        image_plan=result.output.image_plan,
    )
    record = create_build_version(
        project_id,
        design_version_id=design_record["id"],
        provider=payload.selection.provider,
        model=model,
        manifest=manifest,
        export_root_path=export_root_path,
        export_zip_path=export_zip_path,
    )
    complete_generation_run(
        run["id"],
        latency_ms=result.latency_ms,
        token_usage=result.token_usage,
        output_ref_id=record["id"],
    )
    return _build_out(record)


@router.get("/projects/{project_id}/builds/{build_id}", response_model=BuildVersionOut)
async def get_build(project_id: str, build_id: str) -> BuildVersionOut:
    return _build_out(get_build_version(project_id, build_id))


@router.get("/projects/{project_id}/builds/{build_id}/download")
async def download_build(project_id: str, build_id: str) -> FileResponse:
    build = get_build_version(project_id, build_id)
    return FileResponse(
        build["export_zip_path"],
        filename=Path(build["export_zip_path"]).name,
        media_type="application/zip",
    )


@router.get("/projects/{project_id}/image-suggestions", response_model=ImageSuggestionsResponse)
async def get_image_suggestions(project_id: str) -> ImageSuggestionsResponse:
    requirement = get_requirement_version(project_id, None)
    suggestions = build_image_suggestions(project_id, RequirementBrief.model_validate(requirement["brief"]))
    return ImageSuggestionsResponse(project_id=project_id, suggestions=suggestions)
