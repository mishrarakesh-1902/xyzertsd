import os
from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    APP_NAME: str = "WindScope UK Wind Forecast Intelligence"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Elexon BMRS API
    ELEXON_API_BASE_URL: str = "https://data.elexon.co.uk/bmrs/api/v1"
    
    # Cache directory
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    DATA_CACHE_DIR: str = str(BASE_DIR / "data" / "cache")
    
    # CORS
    CORS_ORIGINS: str = "*"

    @property
    def cors_origins_list(self) -> List[str]:
        if not self.CORS_ORIGINS or self.CORS_ORIGINS == "*":
            return ["*"]
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
