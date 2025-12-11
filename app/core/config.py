"""
Configuration settings for the application.
Loads environment variables and provides application configuration.
"""

from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    """

    # Application
    APP_NAME: str = "Organization Management Service"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = Field(default="development", env="ENVIRONMENT")
    DEBUG: bool = Field(default=True, env="DEBUG")

    # MongoDB
    MONGODB_URL: str = Field(..., env="MONGODB_URL")
    DATABASE_NAME: str = Field(..., env="DATABASE_NAME")

    # JWT
    SECRET_KEY: str = Field(..., env="SECRET_KEY")
    ALGORITHM: str = Field(default="HS256", env="ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=1440, env="ACCESS_TOKEN_EXPIRE_MINUTES")

    # CORS
    CORS_ORIGINS: str = Field(
        default="http://localhost:3000,http://localhost:8000",
        env="CORS_ORIGINS"
    )

    # Logging
    LOG_LEVEL: str = Field(default="DEBUG", env="LOG_LEVEL")

    @property
    def cors_origins_list(self) -> List[str]:
        """Convert comma-separated CORS origins to list."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    class Config:
        env_file = ".env"
        case_sensitive = True


# Create global settings instance
settings = Settings()
