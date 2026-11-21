import os
from pathlib import Path
from typing import List, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Absolute path to backend directory and dev database (backend/edupulse_dev.db)
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
if os.environ.get("VERCEL"):
    DEV_DB_PATH = Path("/tmp") / "edupulse_dev.db"
else:
    DEV_DB_PATH = BACKEND_DIR / "edupulse_dev.db"
DEFAULT_DEV_DATABASE_URL = f"sqlite:///{DEV_DB_PATH.as_posix()}"


class Settings(BaseSettings):
    PROJECT_NAME: str = "EduPulse"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"
    
    # Server configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Database (defaults to absolute path backend/edupulse_dev.db)
    DATABASE_URL: str = DEFAULT_DEV_DATABASE_URL
    
    # JWT Authentication
    JWT_SECRET: str = "super-secret-jwt-key-min-32-characters-long-edupulse-2026"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15  # 15 minutes
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7  # 7 days
    
    # Rate Limiting
    RATE_LIMIT_LOGIN_PER_MINUTE: int = 5
    
    # Demo Mode
    DEMO_MODE: bool = True
    
    # CORS
    CORS_ORIGINS: Union[List[str], str] = ["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"]
    
    # Language preference storage only (EN / TA) - UI holds actual localized strings
    SUPPORTED_LANGUAGES: List[str] = ["en", "ta"]

    @field_validator("DATABASE_URL", mode="before")
    def resolve_sqlite_path(cls, v: str) -> str:
        if v and v.startswith("sqlite:///"):
            relative_part = v.replace("sqlite:///", "")
            if relative_part and not os.path.isabs(relative_part):
                abs_path = (BACKEND_DIR / relative_part).resolve()
                return f"sqlite:///{abs_path.as_posix()}"
        return v

    @field_validator("CORS_ORIGINS", mode="before")
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, list):
            return v
        return ["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()
