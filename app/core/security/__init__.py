"""
Módulo de Seguridad Avanzada - Gestión de Taller
================================================
Proporciona funcionalidades de seguridad adicionales:
- Rate Limiting
- Auditoría de seguridad
- Validación de entrada
- Middleware de seguridad
- Detección de amenazas
- 2FA/TOTP
"""

from .rate_limiter import (
    RateLimiter,
    login_limiter,
    ip_limiter,
    api_limiter,
    password_reset_limiter,
    registration_limiter
)
from .audit_logger import SecurityAuditLogger, audit_logger, SecurityEventType
from .validators import InputValidator, Sanitizer
from .middleware import SecurityMiddleware, RateLimitMiddleware, get_client_ip
from .exceptions import (
    SecurityException,
    RateLimitExceeded,
    AccountLockedException,
    InvalidInputException,
    SuspiciousActivityException,
    SQLInjectionDetected,
    XSSDetected
)
from .totp import TOTPManager, totp_manager, encrypt_totp_secret, decrypt_totp_secret

__all__ = [
    # Rate Limiting
    'RateLimiter',
    'login_limiter',
    'ip_limiter', 
    'api_limiter',
    'password_reset_limiter',
    'registration_limiter',
    
    # Auditoría
    'SecurityAuditLogger',
    'audit_logger',
    'SecurityEventType',
    
    # Validación
    'InputValidator',
    'Sanitizer',
    
    # Middleware
    'SecurityMiddleware',
    'RateLimitMiddleware',
    'get_client_ip',
    
    # Excepciones
    'SecurityException',
    'RateLimitExceeded',
    'AccountLockedException',
    'InvalidInputException',
    'SuspiciousActivityException',
    'SQLInjectionDetected',
    'XSSDetected',
    
    # 2FA/TOTP
    'TOTPManager',
    'totp_manager',
    'encrypt_totp_secret',
    'decrypt_totp_secret',
]

__version__ = '1.1.0'
