
from typing import List, Union, Any, Optional

from pydantic import AnyHttpUrl, validator
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8 
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 30  # 30 days
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    
    # Variables de Postgres opcionales para permitir SQLite
    POSTGRES_SERVER: Optional[str] = None
    POSTGRES_USER: Optional[str] = None
    POSTGRES_PASSWORD: Optional[str] = None
    POSTGRES_DB: Optional[str] = None
    SQLALCHEMY_DATABASE_URI: str = "sqlite:///./sql_app.db"

    # Configuración SMTP para verificación de email
    SMTP_SERVER: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""

    # ============== CONFIGURACIÓN DE SEGURIDAD ==============
    
    # Rate Limiting - Login
    LOGIN_RATE_LIMIT_MAX_ATTEMPTS: int = 5
    LOGIN_RATE_LIMIT_WINDOW_SECONDS: int = 300  # 5 minutos
    LOGIN_RATE_LIMIT_BLOCK_SECONDS: int = 900   # 15 minutos de bloqueo
    
    # Rate Limiting - API General
    API_RATE_LIMIT_PER_MINUTE: int = 60
    IP_RATE_LIMIT_PER_MINUTE: int = 100
    
    # Rate Limiting - Endpoints sensibles
    PASSWORD_RESET_RATE_LIMIT: int = 3
    REGISTRATION_RATE_LIMIT: int = 5
    
    # Bloqueo de cuenta
    ACCOUNT_LOCKOUT_THRESHOLD: int = 5  # Intentos antes del bloqueo
    ACCOUNT_LOCKOUT_DURATION_MINUTES: int = 30
    
    # Seguridad de contraseñas
    PASSWORD_MIN_LENGTH: int = 8
    PASSWORD_REQUIRE_UPPERCASE: bool = True
    PASSWORD_REQUIRE_LOWERCASE: bool = True
    PASSWORD_REQUIRE_DIGIT: bool = True
    PASSWORD_REQUIRE_SPECIAL: bool = False  # Opcional
    
    # Auditoría
    AUDIT_LOG_ENABLED: bool = True
    AUDIT_LOG_PATH: str = "logs/security_audit.log"
    AUDIT_LOG_MAX_BYTES: int = 10_485_760  # 10 MB
    AUDIT_LOG_BACKUP_COUNT: int = 5
    
    # Headers de seguridad
    SECURITY_HEADERS_ENABLED: bool = True
    
    # Modo debug (desactivar en producción)
    DEBUG_MODE: bool = False


    @validator("SQLALCHEMY_DATABASE_URI", pre=True)
    def assemble_db_connection(cls, v: Union[str, None], values: dict) -> Any:
        if isinstance(v, str) and v:
            return v
        
        # Si no hay URI definida, intentamos armar la de Postgres
        user = values.get('POSTGRES_USER')
        password = values.get('POSTGRES_PASSWORD')
        server = values.get('POSTGRES_SERVER', '127.0.0.1')
        db = values.get('POSTGRES_DB')
        
        if all([user, password, db]):
             return f"postgresql://{user}:{password}@{server}/{db}"
        
        # Fallback por defecto a SQLite para desarrollo sin fricción
        return "sqlite:///./sql_app.db"


    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings()
