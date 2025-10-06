"""
Configuración del microservicio MS-AUTH-PY
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Configuración de la aplicación"""
    
    # API Configuration
    APP_NAME: str = "MS-AUTH-PY - Authentication Service"
    APP_VERSION: str = "1.0.0"
    API_PREFIX: str = "/api/v1/auth"
    DEBUG: bool = False
    
    # Database Configuration
    DATABASE_URL: str = "postgresql://dgt_user:dgt_pass@localhost:5437/digital_twins_db"
    
    # JWT Configuration
    SECRET_KEY: str = "your-secret-key-here-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 horas
    
    # CORS Configuration
    CORS_ORIGINS: list = [
        "http://localhost:3000",
        "http://localhost:8080",
        "http://localhost"
    ]
    
    # Service Configuration
    SERVICE_HOST: str = "0.0.0.0"
    SERVICE_PORT: int = 8000
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Instancia global de configuración
settings = Settings()

