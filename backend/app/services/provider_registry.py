"""Provider registry and catalog helpers."""

from __future__ import annotations

from app.schemas import ProviderCatalogItem
from app.services.providers.base import ClaudeAdapter, DeepSeekAdapter, GeminiAdapter, OpenAIAdapter


class ProviderRegistry:
    def __init__(self) -> None:
        self._providers = {
            "openai": OpenAIAdapter(),
            "gemini": GeminiAdapter(),
            "claude": ClaudeAdapter(),
            "deepseek": DeepSeekAdapter(),
        }

    def get(self, name: str):
        provider = self._providers.get(name)
        if not provider:
            raise KeyError(f"Unknown provider: {name}")
        return provider

    def catalog(self) -> list[ProviderCatalogItem]:
        items: list[ProviderCatalogItem] = []
        for name, provider in self._providers.items():
            items.append(
                ProviderCatalogItem(
                    name=name,  # type: ignore[arg-type]
                    configured=provider.is_configured(),
                    offline_fallback=True,
                    default_models={
                        "requirements": provider.default_model("requirements"),
                        "design": provider.default_model("design"),
                        "build": provider.default_model("build"),
                    },
                )
            )
        return items


provider_registry = ProviderRegistry()
