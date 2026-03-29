"""Application configuration."""

from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Runtime settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Website Generator Platform"
    environment: str = "development"
    debug: bool = True

    admin_username: str = "admin"
    admin_password: str = "change-me"
    session_secret: str = "replace-with-a-long-random-secret"
    session_cookie_name: str = "wgp_session"
    session_ttl_hours: int = 12

    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    data_dir: Path = BASE_DIR / "data"
    storage_root: Path = BASE_DIR / "storage"
    database_path: Path = BASE_DIR / "data" / "website_generator.db"

    max_upload_size_bytes: int = 10 * 1024 * 1024
    allowed_upload_extensions: list[str] = Field(
        default_factory=lambda: [".png", ".jpg", ".jpeg", ".webp", ".svg", ".gif"]
    )

    prompt_template_version: str = "v1"
    real_provider_calls_enabled: bool = False

    openai_api_key: str = ""
    openai_model_refine: str = "gpt-5-mini"
    openai_model_design: str = "gpt-5"
    openai_model_build: str = "gpt-5"

    gemini_api_key: str = ""
    gemini_model_refine: str = "gemini-2.5-flash"
    gemini_model_design: str = "gemini-2.5-pro"
    gemini_model_build: str = "gemini-2.5-pro"

    claude_api_key: str = ""
    claude_model_refine: str = "claude-3-7-sonnet-latest"
    claude_model_design: str = "claude-sonnet-4-0"
    claude_model_build: str = "claude-sonnet-4-0"

    deepseek_api_key: str = ""
    deepseek_model_refine: str = "deepseek-chat"
    deepseek_model_design: str = "deepseek-chat"
    deepseek_model_build: str = "deepseek-chat"

    @property
    def cors_origin_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]

    @property
    def upload_dir(self) -> Path:
        return self.storage_root / "uploads"

    @property
    def export_dir(self) -> Path:
        return self.storage_root / "exports"


settings = Settings()
