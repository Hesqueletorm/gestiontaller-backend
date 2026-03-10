"""
Logger de Auditoría de Seguridad.
Registra todos los eventos de seguridad para análisis y cumplimiento.
"""

import logging
import json
import os
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum
from pathlib import Path
import traceback


class SecurityEventType(str, Enum):
    """Tipos de eventos de seguridad"""
    # Autenticación
    LOGIN_SUCCESS = "LOGIN_SUCCESS"
    LOGIN_FAILED = "LOGIN_FAILED"
    LOGOUT = "LOGOUT"
    TOKEN_REFRESH = "TOKEN_REFRESH"
    TOKEN_INVALID = "TOKEN_INVALID"
    
    # Contraseñas
    PASSWORD_CHANGED = "PASSWORD_CHANGED"
    PASSWORD_RESET_REQUEST = "PASSWORD_RESET_REQUEST"
    PASSWORD_RESET_SUCCESS = "PASSWORD_RESET_SUCCESS"
    PASSWORD_RESET_FAILED = "PASSWORD_RESET_FAILED"
    
    # Cuentas
    ACCOUNT_CREATED = "ACCOUNT_CREATED"
    ACCOUNT_ACTIVATED = "ACCOUNT_ACTIVATED"
    ACCOUNT_DEACTIVATED = "ACCOUNT_DEACTIVATED"
    ACCOUNT_LOCKED = "ACCOUNT_LOCKED"
    ACCOUNT_UNLOCKED = "ACCOUNT_UNLOCKED"
    ACCOUNT_DELETED = "ACCOUNT_DELETED"
    
    # Rate Limiting
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    IP_BLOCKED = "IP_BLOCKED"
    
    # Acceso
    ACCESS_DENIED = "ACCESS_DENIED"
    PERMISSION_DENIED = "PERMISSION_DENIED"
    RESOURCE_ACCESS = "RESOURCE_ACCESS"
    
    # Amenazas
    SQL_INJECTION_ATTEMPT = "SQL_INJECTION_ATTEMPT"
    XSS_ATTEMPT = "XSS_ATTEMPT"
    SUSPICIOUS_ACTIVITY = "SUSPICIOUS_ACTIVITY"
    BRUTE_FORCE_DETECTED = "BRUTE_FORCE_DETECTED"
    
    # Sistema
    CONFIG_CHANGED = "CONFIG_CHANGED"
    ADMIN_ACTION = "ADMIN_ACTION"
    ERROR = "ERROR"


class SecurityAuditLogger:
    """
    Logger de auditoría de seguridad.
    
    Características:
    - Logs estructurados en JSON
    - Rotación de archivos
    - Niveles de severidad
    - Contexto enriquecido
    """
    
    def __init__(
        self,
        log_dir: str = "logs",
        app_name: str = "gestiondetaller",
        log_to_console: bool = True,
        log_to_file: bool = True
    ):
        self.log_dir = Path(log_dir)
        self.app_name = app_name
        self.log_to_console = log_to_console
        self.log_to_file = log_to_file
        
        # Crear directorio de logs
        if log_to_file:
            self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Configurar logger
        self.logger = logging.getLogger(f"security.{app_name}")
        self.logger.setLevel(logging.DEBUG)
        
        # Evitar duplicados
        if not self.logger.handlers:
            self._setup_handlers()
    
    def _setup_handlers(self):
        """Configura los handlers de logging."""
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Console handler
        if self.log_to_console:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
        
        # File handler (JSON)
        if self.log_to_file:
            from logging.handlers import RotatingFileHandler
            
            # Log de seguridad principal
            security_log_path = self.log_dir / f"{self.app_name}_security.log"
            file_handler = RotatingFileHandler(
                security_log_path,
                maxBytes=10*1024*1024,  # 10MB
                backupCount=10,
                encoding='utf-8'
            )
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
            
            # Log JSON estructurado
            json_log_path = self.log_dir / f"{self.app_name}_security.json"
            self.json_handler = RotatingFileHandler(
                json_log_path,
                maxBytes=10*1024*1024,
                backupCount=10,
                encoding='utf-8'
            )
            self.json_handler.setLevel(logging.DEBUG)
    
    def _get_severity(self, event_type: SecurityEventType) -> str:
        """Determina severidad según tipo de evento."""
        high_severity = {
            SecurityEventType.ACCOUNT_LOCKED,
            SecurityEventType.BRUTE_FORCE_DETECTED,
            SecurityEventType.SQL_INJECTION_ATTEMPT,
            SecurityEventType.XSS_ATTEMPT,
            SecurityEventType.SUSPICIOUS_ACTIVITY,
            SecurityEventType.ACCESS_DENIED,
        }
        
        medium_severity = {
            SecurityEventType.LOGIN_FAILED,
            SecurityEventType.RATE_LIMIT_EXCEEDED,
            SecurityEventType.TOKEN_INVALID,
            SecurityEventType.PASSWORD_RESET_FAILED,
            SecurityEventType.PERMISSION_DENIED,
        }
        
        if event_type in high_severity:
            return "HIGH"
        elif event_type in medium_severity:
            return "MEDIUM"
        return "LOW"
    
    def log(
        self,
        event_type: SecurityEventType,
        success: bool = True,
        username: Optional[str] = None,
        user_id: Optional[int] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        lubricentro_id: Optional[int] = None
    ) -> None:
        """
        Registra un evento de seguridad.
        
        Args:
            event_type: Tipo de evento
            success: Si la operación fue exitosa
            username: Nombre de usuario
            user_id: ID del usuario
            ip_address: Dirección IP
            user_agent: User-Agent del navegador
            message: Mensaje descriptivo
            details: Detalles adicionales
            lubricentro_id: ID del lubricentro (multi-tenant)
        """
        timestamp = datetime.utcnow().isoformat() + "Z"
        severity = self._get_severity(event_type)
        
        # Construir evento estructurado
        event = {
            "timestamp": timestamp,
            "event_type": event_type.value,
            "severity": severity,
            "success": success,
            "app": self.app_name,
            "username": username,
            "user_id": user_id,
            "ip_address": ip_address,
            "user_agent": user_agent[:200] if user_agent else None,
            "message": message,
            "lubricentro_id": lubricentro_id,
            "details": details or {}
        }
        
        # Log legible
        log_msg = f"[{event_type.value}] "
        if username:
            log_msg += f"user={username} "
        if ip_address:
            log_msg += f"ip={ip_address} "
        if message:
            log_msg += f"- {message}"
        
        # Nivel de log según resultado y severidad
        if not success or severity == "HIGH":
            self.logger.warning(log_msg)
        else:
            self.logger.info(log_msg)
        
        # Log JSON estructurado
        if self.log_to_file and hasattr(self, 'json_handler'):
            try:
                json_line = json.dumps(event, ensure_ascii=False) + "\n"
                with open(self.json_handler.baseFilename, 'a', encoding='utf-8') as f:
                    f.write(json_line)
            except Exception:
                pass
    
    # Métodos de conveniencia
    def log_login_success(
        self,
        username: str,
        user_id: int = None,
        ip_address: str = None,
        user_agent: str = None,
        lubricentro_id: int = None
    ):
        self.log(
            SecurityEventType.LOGIN_SUCCESS,
            success=True,
            username=username,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            lubricentro_id=lubricentro_id,
            message="Login exitoso"
        )
    
    def log_login_failed(
        self,
        username: str,
        reason: str,
        ip_address: str = None,
        user_agent: str = None,
        attempts_remaining: int = None
    ):
        self.log(
            SecurityEventType.LOGIN_FAILED,
            success=False,
            username=username,
            ip_address=ip_address,
            user_agent=user_agent,
            message=f"Login fallido: {reason}",
            details={"reason": reason, "attempts_remaining": attempts_remaining}
        )
    
    def log_account_locked(
        self,
        username: str,
        ip_address: str = None,
        duration_minutes: int = 15
    ):
        self.log(
            SecurityEventType.ACCOUNT_LOCKED,
            success=False,
            username=username,
            ip_address=ip_address,
            message=f"Cuenta bloqueada por {duration_minutes} minutos",
            details={"lock_duration_minutes": duration_minutes}
        )
    
    def log_rate_limit_exceeded(
        self,
        identifier: str,
        limiter_name: str,
        ip_address: str = None
    ):
        self.log(
            SecurityEventType.RATE_LIMIT_EXCEEDED,
            success=False,
            username=identifier if '@' not in identifier else None,
            ip_address=ip_address or identifier,
            message=f"Rate limit excedido en {limiter_name}",
            details={"limiter": limiter_name}
        )
    
    def log_suspicious_activity(
        self,
        description: str,
        username: str = None,
        ip_address: str = None,
        details: Dict = None
    ):
        self.log(
            SecurityEventType.SUSPICIOUS_ACTIVITY,
            success=False,
            username=username,
            ip_address=ip_address,
            message=description,
            details=details
        )
    
    def log_password_change(
        self,
        username: str,
        user_id: int = None,
        ip_address: str = None,
        success: bool = True
    ):
        self.log(
            SecurityEventType.PASSWORD_CHANGED,
            success=success,
            username=username,
            user_id=user_id,
            ip_address=ip_address,
            message="Contraseña cambiada" if success else "Intento de cambio de contraseña fallido"
        )
    
    def log_sql_injection_attempt(
        self,
        field: str,
        value_preview: str,
        ip_address: str = None,
        username: str = None
    ):
        self.log(
            SecurityEventType.SQL_INJECTION_ATTEMPT,
            success=False,
            username=username,
            ip_address=ip_address,
            message=f"Posible SQL Injection en campo {field}",
            details={"field": field, "value_preview": value_preview[:50]}
        )
    
    def log_xss_attempt(
        self,
        field: str,
        ip_address: str = None,
        username: str = None
    ):
        self.log(
            SecurityEventType.XSS_ATTEMPT,
            success=False,
            username=username,
            ip_address=ip_address,
            message=f"Posible XSS en campo {field}",
            details={"field": field}
        )


# Instancia global
audit_logger = SecurityAuditLogger(
    log_dir="logs",
    app_name="gestiondetaller"
)
