"""
Application Settings and Configuration
"""
from pydantic_settings import BaseSettings
from pydantic import field_validator, model_validator
from typing import List, Optional
import json
from typing import Iterable


class Settings(BaseSettings):
    """Application settings"""
    
    # Server settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True
    
    # MongoDB settings
    MONGODB_URL: str = "mongodb://localhost:27017"
    DATABASE_NAME: str = "company_profiles_db"
    
    # CORS settings - stored as string, converted to list
    CORS_ORIGINS: Optional[str] = None
    
    # API settings
    API_V1_PREFIX: str = "/api/v1"
    
    # File settings
    UPLOAD_DIR: str = "../"
    ALLOWED_EXTENSIONS: List[str] = [".json"]
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    
    # API Keys
    POLYGON_API_KEY: Optional[str] = None
    FINNHUB_API_KEY: Optional[str] = None
    
    # Gemini Scraper settings
    GEMINI_HEADLESS: Optional[str] = "true"  # Default to headless mode
    
    # Proxy settings for rate limiting
    PROXY_SERVER: Optional[str] = None  # Single proxy (backward compatible)
    PROXY_SERVERS: Optional[str] = None  # Comma-separated list of proxies for rotation
    
    @staticmethod
    def _expand_origin(origin: str) -> List[str]:
        """Ensure every origin includes a scheme; generate http/https variants when missing."""
        if not isinstance(origin, str):
            return []
        cleaned = origin.strip().rstrip("/")
        if not cleaned:
            return []
        if cleaned == "*":
            return ["*"]
        if "://" in cleaned:
            return [cleaned]
        return [f"http://{cleaned}", f"https://{cleaned}"]

    @staticmethod
    def _normalize_origins(origins: Iterable[str]) -> List[str]:
        """Deduplicate and normalize origins."""
        normalized = []
        seen = set()
        for origin in origins:
            for expanded in Settings._expand_origin(origin):
                if expanded not in seen:
                    seen.add(expanded)
                    normalized.append(expanded)
        return normalized

    @model_validator(mode='after')
    def parse_cors_origins(self):
        """Parse CORS_ORIGINS from string to list"""
        if self.CORS_ORIGINS is None:
            # Default: allow all origins (development)
            self.CORS_ORIGINS = ["*"]
        elif isinstance(self.CORS_ORIGINS, str):
            # Try JSON first
            try:
                parsed = json.loads(self.CORS_ORIGINS)
                if isinstance(parsed, list):
                    self.CORS_ORIGINS = parsed
                else:
                    # If not a list, treat as comma-separated
                    self.CORS_ORIGINS = [origin.strip() for origin in self.CORS_ORIGINS.split(',') if origin.strip()]
            except (json.JSONDecodeError, ValueError):
                # If not JSON, treat as comma-separated string
                self.CORS_ORIGINS = [origin.strip() for origin in self.CORS_ORIGINS.split(',') if origin.strip()]
        # If it's already a list, keep it as is
        if isinstance(self.CORS_ORIGINS, list):
            if "*" in self.CORS_ORIGINS:
                self.CORS_ORIGINS = ["*"]
            else:
                self.CORS_ORIGINS = self._normalize_origins(self.CORS_ORIGINS)
        return self
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Get CORS origins as a list"""
        if isinstance(self.CORS_ORIGINS, list):
            return self.CORS_ORIGINS
        return []
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Create settings instance
settings = Settings()
