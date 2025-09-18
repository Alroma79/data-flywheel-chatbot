"""
Configuration management for the Data Flywheel Chatbot application.
Loads & validates environment variables.
"""

from functools import lru_cache
from typing import List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import uuid


class Settings(BaseSettings):
    # --- Meta
    app_name: str = "Data Flywheel Chatbot API"
    debug: bool = Field(default=False, alias="DEBUG")
    
    # --- Demo Mode
    demo_mode: bool = Field(default=False, alias="DEMO_MODE")
    app_version: str = Field(default="v0.3-interview", alias="APP_VERSION")

    # --- Database
    # note: prefer absolute path for sqlite in prod; keep as-is for dev
    database_url: str = Field(default="sqlite:///./backend/chatbot.db", alias="DATABASE_URL")

    @classmethod
    def _override_database_url(cls, url):
        cls.database_url = url

    # --- OpenAI
    openai_api_key: str = Field(alias="OPENAI_API_KEY")
    default_model: str = Field(default="gpt-4o", alias="DEFAULT_MODEL")
    default_temperature: float = Field(default=0.7, alias="DEFAULT_TEMPERATURE")
    max_tokens: Optional[int] = Field(default=None, alias="MAX_TOKENS")

    # --- CORS
    cors_origins: List[str] = Field(
        default_factory=lambda: ["http://localhost:8000"],
        alias="CORS_ORIGINS"
    )
    cors_credentials: bool = Field(default=True, alias="CORS_CREDENTIALS")
    cors_methods: List[str] = Field(default_factory=lambda: ["*"], alias="CORS_METHODS")
    cors_headers: List[str] = Field(default_factory=lambda: ["*"], alias="CORS_HEADERS")

    # --- Chat Settings
    max_context_messages: int = Field(default=10, alias="MAX_CONTEXT_MESSAGES", description="Maximum number of messages to include in context window")

    # --- Security
    app_token: Optional[str] = Field(default=None, alias="APP_TOKEN")

    # --- Rate limiting (not enforced yet)
    rate_limit_requests: int = Field(default=100, alias="RATE_LIMIT_REQUESTS")
    rate_limit_window: int = Field(default=3600, alias="RATE_LIMIT_WINDOW")  # seconds

    # --- Logging
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    log_format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        alias="LOG_FORMAT",
    )

    # Pydantic v2 config
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ----- Validators (v2 style) -----
    @field_validator("cors_origins", "cors_methods", "cors_headers", mode="before")
    @classmethod
    def _parse_csv_to_list(cls, v):
        # Accept comma-separated string or list
        if isinstance(v, str):
            return [item.strip() for item in v.split(",") if item.strip()]
        return v

    @field_validator("database_url")
    @classmethod
    def _require_db_url(cls, v: str) -> str:
        if not v:
            raise ValueError("DATABASE_URL is required")
        return v

    @field_validator("openai_api_key")
    @classmethod
    def _require_openai_key(cls, v: str) -> str:
        if not v:
            raise ValueError("OPENAI_API_KEY is required")
        return v

    @field_validator("default_temperature")
    @classmethod
    def _check_temperature(cls, v: float) -> float:
        if not (0 <= v <= 2):
            raise ValueError("DEFAULT_TEMPERATURE must be between 0 and 2")
        return v


def get_settings() -> Settings:
    return Settings()
