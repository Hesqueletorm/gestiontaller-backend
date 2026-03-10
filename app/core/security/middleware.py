"""
Middleware de seguridad para FastAPI.
Integra rate limiting, logging y protección contra amenazas.
"""

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import time
from typing import Callable

from .rate_limiter import ip_limiter, api_limiter
from .audit_logger import audit_logger, SecurityEventType
from .exceptions import RateLimitExceeded


class SecurityMiddleware(BaseHTTPMiddleware):
    """
    Middleware de seguridad que:
    - Aplica rate limiting por IP
    - Registra requests sospechosos
    - Añade headers de seguridad
    - Mide tiempos de respuesta
    """
    
    def __init__(
        self,
        app: ASGIApp,
        enable_rate_limit: bool = True,
        enable_security_headers: bool = True,
        excluded_paths: list = None
    ):
        super().__init__(app)
        self.enable_rate_limit = enable_rate_limit
        self.enable_security_headers = enable_security_headers
        self.excluded_paths = excluded_paths or [
            "/docs",
            "/redoc",
            "/openapi.json",
            "/health",
            "/favicon.ico"
        ]
    
    async def dispatch(
        self,
        request: Request,
        call_next: Callable
    ) -> Response:
        # Obtener IP del cliente
        client_ip = self._get_client_ip(request)
        path = request.url.path
        
        # Excluir paths
        if any(path.startswith(excluded) for excluded in self.excluded_paths):
            return await call_next(request)
        
        # Rate limiting por IP
        if self.enable_rate_limit:
            if not ip_limiter.is_allowed(client_ip):
                audit_logger.log_rate_limit_exceeded(
                    identifier=client_ip,
                    limiter_name="ip",
                    ip_address=client_ip
                )
                raise RateLimitExceeded(
                    retry_after=ip_limiter.get_retry_after(client_ip)
                )
            ip_limiter.record_attempt(client_ip)
        
        # Medir tiempo
        start_time = time.time()
        
        # Procesar request
        response = await call_next(request)
        
        # Calcular duración
        duration = time.time() - start_time
        
        # Añadir headers de seguridad
        if self.enable_security_headers:
            self._add_security_headers(response)
        
        # Header de tiempo de proceso
        response.headers["X-Process-Time"] = f"{duration:.4f}"
        
        # Log de requests lentos (> 5 segundos)
        if duration > 5:
            audit_logger.log(
                SecurityEventType.SUSPICIOUS_ACTIVITY,
                success=True,
                ip_address=client_ip,
                message=f"Request lento: {path} ({duration:.2f}s)",
                details={"path": path, "duration": duration, "method": request.method}
            )
        
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """Obtiene IP real del cliente (considerando proxies)."""
        # X-Forwarded-For (puede tener múltiples IPs)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Tomar la primera IP (cliente original)
            return forwarded_for.split(",")[0].strip()
        
        # X-Real-IP
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # IP directa
        if request.client:
            return request.client.host
        
        return "unknown"
    
    def _add_security_headers(self, response: Response) -> None:
        """Añade headers de seguridad estándar."""
        headers = {
            # Prevenir clickjacking
            "X-Frame-Options": "DENY",
            
            # Prevenir MIME sniffing
            "X-Content-Type-Options": "nosniff",
            
            # Habilitar XSS filter del navegador
            "X-XSS-Protection": "1; mode=block",
            
            # Referrer policy
            "Referrer-Policy": "strict-origin-when-cross-origin",
            
            # Permissions policy
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
            
            # Content Security Policy básica
            "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'",
        }
        
        for header, value in headers.items():
            if header not in response.headers:
                response.headers[header] = value


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware específico de rate limiting para endpoints de API.
    Más estricto que el rate limiting por IP.
    """
    
    def __init__(
        self,
        app: ASGIApp,
        requests_per_minute: int = 100,
        exempt_paths: list = None
    ):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.exempt_paths = exempt_paths or []
        # Diccionario simple para tracking de requests
        self._requests: dict = {}
    
    def _is_rate_limited(self, identifier: str) -> bool:
        """Verifica si el identifier está rate limited."""
        current_time = time.time()
        window_start = current_time - 60  # Ventana de 1 minuto
        
        if identifier not in self._requests:
            self._requests[identifier] = []
        
        # Limpiar requests antiguos
        self._requests[identifier] = [
            t for t in self._requests[identifier] if t > window_start
        ]
        
        # Verificar límite
        if len(self._requests[identifier]) >= self.requests_per_minute:
            return True
        
        # Registrar request
        self._requests[identifier].append(current_time)
        return False
    
    async def dispatch(
        self,
        request: Request,
        call_next: Callable
    ) -> Response:
        path = request.url.path
        
        # Excluir paths específicos
        if any(path.startswith(exempt) for exempt in self.exempt_paths):
            return await call_next(request)
        
        # Solo aplicar a /api/
        if not path.startswith("/api/"):
            return await call_next(request)
        
        client_ip = request.client.host if request.client else "unknown"
        identifier = f"{client_ip}"
        
        if self._is_rate_limited(identifier):
            raise RateLimitExceeded(
                retry_after=60,
                detail="Rate limit excedido. Por favor espere un momento."
            )
        
        return await call_next(request)


def get_client_ip(request: Request) -> str:
    """
    Función de utilidad para obtener IP del cliente.
    Usar como dependencia en endpoints.
    """
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    if request.client:
        return request.client.host
    
    return "unknown"
