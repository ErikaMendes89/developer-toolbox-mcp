from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration. No credentials are required for the initial release."""

    model_config = SettingsConfigDict(env_prefix="TOOLBOX_", env_file=".env", extra="ignore")

    workspace_root: Path = Field(default=Path.cwd())
    max_file_bytes: int = Field(default=256_000, ge=1, le=2_000_000)
    max_search_results: int = Field(default=50, ge=1, le=200)


settings = Settings()
