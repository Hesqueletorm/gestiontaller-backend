"""
Endpoints de Salud y Métricas de Seguridad
"""
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api import deps
from app.core.config import settings
from app.core.security.rate_limiter import login_limiter, ip_limiter
from app.models.user import User

router = APIRouter()


class HealthResponse(BaseModel):
    """Respuesta del endpoint de salud"""
    status: str
    timestamp: str
    version: str = "1.0.0"
    

class SecurityStatusResponse(BaseModel):
    """Estado de seguridad del sistema (solo para admins)"""
    security_headers_enabled: bool
    rate_limiting_enabled: bool
    audit_logging_enabled: bool
    login_rate_limit: dict
    api_rate_limit: dict
    blocked_ips_count: int


@router.get("/health", response_model=HealthResponse)
def health_check() -> Any:
    """
    Endpoint de salud - verifica que la API está funcionando.
    No requiere autenticación.
    """
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        version="1.0.0"
    )


@router.get("/security-status", response_model=SecurityStatusResponse)
def security_status(
    current_user: User = Depends(deps.get_current_active_admin)
) -> Any:
    """
    Estado de seguridad del sistema.
    Solo accesible por administradores.
    
    Muestra:
    - Configuración de seguridad activa
    - Estado de rate limiters
    - Conteo de IPs bloqueadas
    """
    return SecurityStatusResponse(
        security_headers_enabled=settings.SECURITY_HEADERS_ENABLED,
        rate_limiting_enabled=True,
        audit_logging_enabled=settings.AUDIT_LOG_ENABLED,
        login_rate_limit={
            "max_attempts": login_limiter.max_attempts,
            "window_seconds": login_limiter.window_seconds,
            "block_seconds": login_limiter.block_seconds,
            "active_blocks": len([k for k in login_limiter._blocked if login_limiter.is_blocked(k)])
        },
        api_rate_limit={
            "requests_per_minute": ip_limiter.max_attempts,
            "active_limits": len(ip_limiter._attempts)
        },
        blocked_ips_count=len([k for k in login_limiter._blocked if login_limiter.is_blocked(k)])
    )
