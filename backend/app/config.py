import os
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    PROJECT_NAME: str = "Chronicle Runtime"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    
    # Database
    DATABASE_URL: str = Field(
        default="sqlite+aiosqlite:///chronicle.db",
        description="Database connection string (SQLite for offline dev/tests, PostgreSQL asyncpg in production)"
    )
    
    # Storage
    BLOB_STORAGE_PATH: str = Field(
        default="/tmp/chronicle_blobs",
        description="Local directory for BLAKE3 content-addressed filesystem deltas"
    )
    
    # LLM Settings
    DEFAULT_LLM_PROVIDER: str = Field(default="offline", description="offline, openai, anthropic, gemini")
    OPENAI_API_KEY: str | None = None
    ANTHROPIC_API_KEY: str | None = None
    GEMINI_API_KEY: str | None = None
    
    # Determinism
    ENABLE_STRICT_CLOCK: bool = True
    ENABLE_FS_RECORDING: bool = True

    class Config:
        env_file = ".env"
        extra = "allow"

settings = Settings()
os.makedirs(settings.BLOB_STORAGE_PATH, exist_ok=True)
