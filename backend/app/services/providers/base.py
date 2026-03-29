"""Provider abstraction layer."""

from __future__ import annotations

from dataclasses import dataclass

from app.config import settings
from app.schemas import DesignSpec, RequirementBrief, RequirementInput
from app.services.providers import template_engine


@dataclass
class ProviderRunResult:
    output: object
    latency_ms: int
    token_usage: dict[str, int]


class BaseProviderAdapter:
    """Normalized provider interface across OpenAI, Gemini, Claude, and DeepSeek."""

    provider_name: str = "openai"

    def default_model(self, stage: str) -> str:
        raise NotImplementedError

    def is_configured(self) -> bool:
        raise NotImplementedError

    async def refine_requirements(
        self,
        *,
        project_name: str,
        payload: RequirementInput,
        asset_filenames: list[str],
        model: str,
    ) -> ProviderRunResult:
        brief = template_engine.build_requirement_brief(project_name, payload, asset_filenames)
        usage = {"input_tokens": 900, "output_tokens": 280}
        return ProviderRunResult(output=brief, latency_ms=80, token_usage=usage)

    async def generate_design(
        self,
        *,
        brief: RequirementBrief,
        asset_filenames: list[str],
        model: str,
    ) -> ProviderRunResult:
        design = template_engine.build_design_spec(brief, asset_filenames)
        usage = {"input_tokens": 1200, "output_tokens": 420}
        return ProviderRunResult(output=design, latency_ms=90, token_usage=usage)

    async def generate_code(
        self,
        *,
        design: DesignSpec,
        asset_filenames: list[str],
        model: str,
    ) -> ProviderRunResult:
        usage = {"input_tokens": 1500, "output_tokens": 640}
        return ProviderRunResult(output=design, latency_ms=110, token_usage=usage)


class OpenAIAdapter(BaseProviderAdapter):
    provider_name = "openai"

    def default_model(self, stage: str) -> str:
        return {
            "requirements": settings.openai_model_refine,
            "design": settings.openai_model_design,
            "build": settings.openai_model_build,
        }[stage]

    def is_configured(self) -> bool:
        return bool(settings.openai_api_key)


class GeminiAdapter(BaseProviderAdapter):
    provider_name = "gemini"

    def default_model(self, stage: str) -> str:
        return {
            "requirements": settings.gemini_model_refine,
            "design": settings.gemini_model_design,
            "build": settings.gemini_model_build,
        }[stage]

    def is_configured(self) -> bool:
        return bool(settings.gemini_api_key)


class ClaudeAdapter(BaseProviderAdapter):
    provider_name = "claude"

    def default_model(self, stage: str) -> str:
        return {
            "requirements": settings.claude_model_refine,
            "design": settings.claude_model_design,
            "build": settings.claude_model_build,
        }[stage]

    def is_configured(self) -> bool:
        return bool(settings.claude_api_key)


class DeepSeekAdapter(BaseProviderAdapter):
    provider_name = "deepseek"

    def default_model(self, stage: str) -> str:
        return {
            "requirements": settings.deepseek_model_refine,
            "design": settings.deepseek_model_design,
            "build": settings.deepseek_model_build,
        }[stage]

    def is_configured(self) -> bool:
        return bool(settings.deepseek_api_key)
