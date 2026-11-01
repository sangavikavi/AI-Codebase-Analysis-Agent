from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    secret_key: str = "super-secret-jwt-encryption-key-change-in-production-123456789"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440

    database_url: str = "sqlite+aiosqlite:///./codebase_analysis.db"

    storage_dir: str = "./storage"
    upload_dir: str = "./storage/uploads"
    repos_dir: str = "./storage/repos"
    exports_dir: str = "./storage/exports"
    max_upload_size_mb: int = 100

    llm_provider: str = "heuristic"
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    gemini_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

    search_provider: str = "duckduckgo"
    tavily_api_key: str = ""

    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    langfuse_host: str = "https://cloud.langfuse.com"
    langfuse_enabled: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    def ensure_directories(self) -> None:
        """Ensure all required storage directories exist."""
        for path_str in [self.storage_dir, self.upload_dir, self.repos_dir, self.exports_dir]:
            p = Path(path_str)
            p.mkdir(parents=True, exist_ok=True)


settings = Settings()
settings.ensure_directories()
