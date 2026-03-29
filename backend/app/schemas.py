"""Pydantic models for API requests and responses."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


StageName = Literal["requirements", "design", "build"]
ProviderName = Literal["openai", "gemini", "claude", "deepseek"]


class LoginRequest(BaseModel):
    username: str
    password: str


class AuthStatusResponse(BaseModel):
    ok: bool
    username: str | None = None


class ProjectCreateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    summary: str | None = Field(default=None, max_length=500)


class ProjectSummary(BaseModel):
    id: str
    name: str
    summary: str | None = None
    created_at: datetime
    updated_at: datetime
    active_requirement_version_id: str | None = None
    active_design_version_id: str | None = None
    active_build_version_id: str | None = None


class StageSelection(BaseModel):
    provider: ProviderName = "openai"
    model: str | None = None


class PagePlan(BaseModel):
    slug: str
    title: str
    goal: str
    sections: list[str]


class AssetReference(BaseModel):
    kind: Literal["uploaded", "placeholder", "internet-suggestion"]
    label: str
    source_type: Literal["project-upload", "placeholder", "recommended-source"]
    asset_id: str | None = None
    page_slug: str | None = None
    section: str | None = None
    alt_text: str | None = None
    notes: str | None = None


class RequirementInput(BaseModel):
    prompt: str = Field(min_length=10)
    business_name: str | None = None
    business_type: str | None = None
    site_type: Literal["landing", "brochure", "campaign", "portfolio"] = "brochure"
    target_audience: list[str] = Field(default_factory=list)
    brand_direction: str | None = None
    required_sections: list[str] = Field(default_factory=list)
    cta_goals: list[str] = Field(default_factory=list)
    reference_notes: str | None = None
    preferred_page_count: int = Field(default=1, ge=1, le=5)
    uploaded_asset_ids: list[str] = Field(default_factory=list)


class RefineRequirementsRequest(BaseModel):
    selection: StageSelection = Field(default_factory=StageSelection)
    input: RequirementInput


class RequirementBrief(BaseModel):
    project_name: str
    project_type: str
    summary: str
    business_context: str
    target_audience: list[str]
    value_propositions: list[str]
    recommended_tone: list[str]
    required_pages: list[PagePlan]
    content_requirements: list[str]
    asset_requirements: list[str]
    assumptions: list[str]
    open_questions: list[str]


class RequirementVersionOut(BaseModel):
    id: str
    version_number: int
    status: str
    approved: bool
    provider: ProviderName
    model: str
    created_at: datetime
    approved_at: datetime | None = None
    source_input: RequirementInput
    brief: RequirementBrief


class DesignPageSection(BaseModel):
    name: str
    purpose: str
    layout: str
    content_items: list[str]
    cta: str | None = None


class DesignPage(BaseModel):
    slug: str
    title: str
    hero_message: str
    sections: list[DesignPageSection]


class VisualDirection(BaseModel):
    mood: str
    colors: list[str]
    typography: str
    layout_keywords: list[str]


class ComponentSpec(BaseModel):
    name: str
    purpose: str
    page_slug: str
    notes: str


class DesignSpec(BaseModel):
    project_name: str
    sitemap: list[str]
    pages: list[DesignPage]
    visual_direction: VisualDirection
    components: list[ComponentSpec]
    image_plan: list[AssetReference]
    content_strategy: list[str]
    implementation_notes: list[str]


class GenerateDesignRequest(BaseModel):
    selection: StageSelection = Field(default_factory=StageSelection)
    requirement_version_id: str | None = None


class DesignVersionOut(BaseModel):
    id: str
    requirement_version_id: str
    version_number: int
    status: str
    approved: bool
    provider: ProviderName
    model: str
    created_at: datetime
    approved_at: datetime | None = None
    design: DesignSpec


class BuildManifest(BaseModel):
    project_name: str
    build_id: str
    site_title: str
    generated_at: datetime
    provider: ProviderName
    model: str
    pages: list[str]
    files: list[str]
    assets: list[AssetReference]
    notes: list[str]


class GenerateBuildRequest(BaseModel):
    selection: StageSelection = Field(default_factory=StageSelection)
    design_version_id: str | None = None


class BuildVersionOut(BaseModel):
    id: str
    design_version_id: str
    version_number: int
    status: str
    provider: ProviderName
    model: str
    created_at: datetime
    completed_at: datetime | None = None
    manifest: BuildManifest
    export_root_path: str
    export_zip_path: str


class UploadedAssetOut(BaseModel):
    id: str
    filename: str
    content_type: str
    size_bytes: int
    storage_path: str
    created_at: datetime


class GenerationRunSummary(BaseModel):
    id: str
    stage: StageName
    provider: ProviderName
    model: str
    prompt_version: str
    status: str
    latency_ms: int
    token_usage: dict[str, int]
    error_message: str | None = None
    output_ref_id: str | None = None
    created_at: datetime
    completed_at: datetime | None = None


class ProjectDetail(ProjectSummary):
    assets: list[UploadedAssetOut] = Field(default_factory=list)
    requirement_versions: list[RequirementVersionOut] = Field(default_factory=list)
    design_versions: list[DesignVersionOut] = Field(default_factory=list)
    build_versions: list[BuildVersionOut] = Field(default_factory=list)
    generation_runs: list[GenerationRunSummary] = Field(default_factory=list)


class ProviderCatalogItem(BaseModel):
    name: ProviderName
    configured: bool
    offline_fallback: bool
    default_models: dict[StageName, str]


class ProviderCatalogResponse(BaseModel):
    providers: list[ProviderCatalogItem]


class ApproveVersionResponse(BaseModel):
    ok: bool
    project_id: str
    approved_version_id: str


class ImageSuggestion(BaseModel):
    source_name: str
    url: str
    licensing_note: str
    intended_use: str
    query: str


class ImageSuggestionsResponse(BaseModel):
    project_id: str
    suggestions: list[ImageSuggestion]


class BuildDownloadResponse(BaseModel):
    ok: bool
    url: str


class StoredRecord(BaseModel):
    """Light helper model for internal mapping."""

    data: dict[str, Any]
