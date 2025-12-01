"""
Application configuration using Pydantic Settings
"""
from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Application
    app_name: str = Field(default="Classroom Downloader API")
    app_version: str = Field(default="1.0.0")
    debug: bool = Field(default=False)

    # Server
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8001)

    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://user:pass@localhost:5432/classroom",
        description="PostgreSQL connection string",
    )

    # Google OAuth2
    google_client_id: str = Field(..., description="Google OAuth2 client ID")
    google_client_secret: str = Field(..., description="Google OAuth2 client secret")
    google_redirect_uri: str = Field(
        default="http://localhost:8001/auth/callback",
        description="OAuth2 redirect URI",
    )
    google_scopes: list[str] = Field(
        default=[
            "https://www.googleapis.com/auth/classroom.courses.readonly",
            "https://www.googleapis.com/auth/classroom.coursework.students.readonly",
            "https://www.googleapis.com/auth/drive.readonly",
        ]
    )

    # Security
    encryption_key: str = Field(..., description="Fernet encryption key for credentials")

    # Downloads
    download_dir: str = Field(default="/app/downloads", description="Directory for downloaded videos")
    max_concurrent_downloads: int = Field(default=5, description="Max simultaneous downloads")
    download_timeout_seconds: int = Field(default=3600, description="Download timeout (1 hour)")

    # Workers
    worker_poll_interval_seconds: int = Field(default=5, description="Worker queue polling interval")
    worker_max_retries: int = Field(default=3, description="Max download retries")

    # Logging
    log_level: str = Field(default="INFO", description="Logging level")
    log_format: str = Field(
        default="text",
        description="Log format: 'text' for development, 'json' for production",
    )
    log_redact_fields: list[str] = Field(
        default_factory=list,
        description="Additional field names to redact in logs",
    )

    # Security
    admin_api_token: str | None = Field(
        default=None,
        description="Admin API token for protected endpoints",
    )
    backend_cors_origins: list[str] = Field(
        default_factory=list,
        description="CORS allowed origins (leave empty for default)",
    )
    force_https_redirect: bool | None = Field(
        default=None,
        description="Force HTTPS redirect (auto-enabled in production)",
    )

    # yt-dlp Configuration
    ytdlp_format: str = Field(
        default="bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        description="yt-dlp format selector",
    )
    ytdlp_output_template: str = Field(
        default="%(id)s.%(ext)s",
        description="yt-dlp output filename template",
    )

    @property
    def download_path(self) -> Path:
        """Get download directory as Path object"""
        return Path(self.download_dir)

    @property
    def environment(self) -> str:
        """Determine environment based on debug flag"""
        return "development" if self.debug else "production"

    @property
    def allowed_cors_origins(self) -> list[str]:
        """Get CORS origins with defaults based on environment"""
        if self.backend_cors_origins:
            return self.backend_cors_origins
        # Default: localhost in development, empty in production
        if self.environment == "development":
            return ["http://localhost:3000", "http://localhost:8001"]
        return []


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance

    Returns:
        Settings instance
    """
    return Settings()
