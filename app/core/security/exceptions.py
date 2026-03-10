"""
Excepciones de seguridad personalizadas.
"""

from fastapi import HTTPException, status


class SecurityException(Exception):
    """Excepción base de seguridad"""
    def __init__(self, message: str = "Error de seguridad"):
        self.message = message
        super().__init__(self.message)


class RateLimitExceeded(HTTPException):
    """Se excedió el límite de intentos"""
    def __init__(self, retry_after: int = 60, detail: str = None):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=detail or f"Demasiados intentos. Intente de nuevo en {retry_after} segundos.",
            headers={"Retry-After": str(retry_after)}
        )
        self.retry_after = retry_after


class AccountLockedException(HTTPException):
    """Cuenta bloqueada por intentos fallidos"""
    def __init__(self, minutes_remaining: int = 15):
        super().__init__(
            status_code=status.HTTP_423_LOCKED,
            detail=f"Cuenta bloqueada por seguridad. Intente de nuevo en {minutes_remaining} minutos."
        )
        self.minutes_remaining = minutes_remaining


class InvalidInputException(HTTPException):
    """Entrada inválida o potencialmente maliciosa"""
    def __init__(self, field: str, reason: str = "Entrada inválida"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Campo '{field}': {reason}"
        )
        self.field = field
        self.reason = reason


class SuspiciousActivityException(HTTPException):
    """Actividad sospechosa detectada"""
    def __init__(self, detail: str = "Actividad sospechosa detectada"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )


class SQLInjectionDetected(InvalidInputException):
    """Posible intento de SQL Injection"""
    def __init__(self, field: str):
        super().__init__(
            field=field,
            reason="Contenido no permitido detectado"
        )


class XSSDetected(InvalidInputException):
    """Posible intento de XSS"""
    def __init__(self, field: str):
        super().__init__(
            field=field,
            reason="Contenido potencialmente peligroso detectado"
        )
