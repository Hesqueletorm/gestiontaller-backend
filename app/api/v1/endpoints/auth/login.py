"""
Endpoints de Login y Token
Con seguridad mejorada: rate limiting, bloqueo de cuentas, auditoría, 2FA, token blacklist
"""
from datetime import timedelta
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from jose import jwt, JWTError
from pydantic import BaseModel

from app.api import deps
from app.core import auth as security
from app.core.config import settings
from app.core.auth import ALGORITHM, blacklist_token, verify_token_not_blacklisted
from app.crud.crud_user import user as crud_user
from app.crud.crud_lubricentro import lubricentro as crud_lubricentro
from app.schemas.token import Token
from app.schemas.lubricentro import LubricentroSimple, LubricentroListResponse

# Importar módulo de seguridad avanzada
from app.core.security.rate_limiter import login_limiter
from app.core.security.audit_logger import audit_logger
from app.core.security.exceptions import RateLimitExceeded, AccountLockedException
from app.core.security.middleware import get_client_ip
from app.core.security.totp import totp_manager, decrypt_totp_secret

router = APIRouter()


# ============== SCHEMAS ADICIONALES ==============

class LoginWith2FARequest(BaseModel):
    """Request para login con 2FA"""
    username: str
    password: str
    totp_code: Optional[str] = None
    lubricentro_id: Optional[int] = None


class LoginResponse(BaseModel):
    """Respuesta de login (puede requerir 2FA)"""
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    requires_2fa: bool = False
    message: Optional[str] = None


# ============== ENDPOINTS ==============

@router.get("/lubricentros", response_model=LubricentroListResponse)
def listar_lubricentros_disponibles(
    db: Session = Depends(deps.get_db)
) -> Any:
    """
    Listar lubricentros disponibles para unirse (para el formulario de registro)
    """
    lubricentros = crud_lubricentro.listar(db, solo_activos=True)
    return LubricentroListResponse(
        lubricentros=[
            LubricentroSimple(id=l.id, nombre=l.nombre, codigo=l.codigo)
            for l in lubricentros
        ]
    )


@router.post("/access-token", response_model=LoginResponse)
def login_access_token(
    request: Request,
    db: Session = Depends(deps.get_db), 
    form_data: OAuth2PasswordRequestForm = Depends(),
    lubricentro_id: Optional[int] = None,
    totp_code: Optional[str] = None
) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests.
    
    Seguridad:
    - Rate limiting por usuario
    - Bloqueo de cuenta en DB tras intentos fallidos
    - Soporte para 2FA/TOTP
    - Auditoría de eventos de login
    """
    # Obtener IP del cliente
    client_ip = get_client_ip(request)
    user_agent = request.headers.get("User-Agent", "")
    
    # Identificador para rate limiting (usuario + IP)
    rate_limit_key = f"{form_data.username}:{client_ip}"
    
    # Verificar rate limiting
    if not login_limiter.is_allowed(rate_limit_key):
        retry_after = login_limiter.get_retry_after(rate_limit_key)
        audit_logger.log_rate_limit_exceeded(
            identifier=form_data.username,
            limiter_name="login",
            ip_address=client_ip
        )
        raise RateLimitExceeded(retry_after=retry_after)
    
    print(f"[LOGIN] Intento de login: usuario='{form_data.username}', lubricentro_id={lubricentro_id}, ip={client_ip}")
    
    # Buscar usuario primero (para verificar bloqueo en DB)
    user = crud_user.get_by_username_for_auth(db, username=form_data.username, lubricentro_id=lubricentro_id)
    
    # Verificar bloqueo de cuenta en DB
    if user and user.is_locked():
        from datetime import datetime
        remaining = int((user.locked_until - datetime.utcnow()).total_seconds() / 60)
        audit_logger.log_login_failed(
            username=form_data.username,
            reason="Cuenta bloqueada",
            ip_address=client_ip,
            user_agent=user_agent
        )
        raise AccountLockedException(minutes_remaining=max(1, remaining))
    
    # Intentar autenticar
    authenticated_user = crud_user.authenticate(
        db, username=form_data.username, password=form_data.password, lubricentro_id=lubricentro_id
    )
    
    if not authenticated_user:
        # Registrar intento fallido en rate limiter
        login_limiter.record_attempt(rate_limit_key, success=False)
        remaining = login_limiter.get_remaining_attempts(rate_limit_key)
        
        # También registrar en DB si el usuario existe
        if user:
            user.record_failed_login()
            # Bloquear cuenta si excede umbral
            if user.failed_login_attempts >= settings.ACCOUNT_LOCKOUT_THRESHOLD:
                user.lock_account(minutes=settings.ACCOUNT_LOCKOUT_DURATION_MINUTES)
                audit_logger.log_account_locked(
                    username=form_data.username,
                    user_id=user.id,
                    ip_address=client_ip,
                    duration_minutes=settings.ACCOUNT_LOCKOUT_DURATION_MINUTES
                )
            db.commit()
        
        audit_logger.log_login_failed(
            username=form_data.username,
            reason="Credenciales inválidas",
            ip_address=client_ip,
            user_agent=user_agent,
            attempts_remaining=remaining
        )
        
        print(f"[LOGIN] Falló autenticación para '{form_data.username}' - {remaining} intentos restantes")
        
        # Si se bloqueó por rate limiter, dar mensaje específico
        if login_limiter.is_blocked(rate_limit_key):
            minutes = login_limiter.get_block_remaining(rate_limit_key)
            raise AccountLockedException(minutes_remaining=minutes)
        
        raise HTTPException(status_code=400, detail="Usuario o contraseña incorrectos")
    
    user = authenticated_user
    
    if not user.activo:
        audit_logger.log_login_failed(
            username=form_data.username,
            reason="Usuario bloqueado por la empresa",
            ip_address=client_ip
        )
        raise HTTPException(
            status_code=403, 
            detail="Tu cuenta ha sido desactivada por la empresa. Contacta con el administrador para más información."
        )
    
    if not getattr(user, 'aprobado', True):
        audit_logger.log_login_failed(
            username=form_data.username,
            reason="Pendiente de aprobación",
            ip_address=client_ip
        )
        raise HTTPException(
            status_code=403, 
            detail="Tu cuenta está pendiente de aprobación. Por favor, espera a que el administrador apruebe tu solicitud."
        )
    
    # Verificar si el lubricentro está activo (solo si el usuario tiene lubricentro asignado)
    if user.lubricentro_id:
        from app.crud.crud_lubricentro import obtener_lubricentro
        lubricentro = obtener_lubricentro(db, user.lubricentro_id)
        if lubricentro and not lubricentro.activo:
            audit_logger.log_login_failed(
                username=form_data.username,
                reason="Taller pendiente de aprobación",
                ip_address=client_ip
            )
            raise HTTPException(
                status_code=403, 
                detail="Tu taller está pendiente de aprobación. Por favor, espera a que el administrador apruebe tu solicitud."
            )
    
    # ============== VERIFICACIÓN 2FA ==============
    if user.totp_enabled:
        if not totp_code:
            # Usuario tiene 2FA, pero no envió código
            return LoginResponse(
                requires_2fa=True,
                message="Se requiere código de autenticación de dos factores"
            )
        
        # Verificar código TOTP
        try:
            secret = decrypt_totp_secret(user.totp_secret, settings.SECRET_KEY)
            if not totp_manager.verify_code(secret, totp_code):
                # Intentar con backup code
                valid, updated_codes = totp_manager.verify_backup_code(
                    user.totp_backup_codes, totp_code
                )
                if valid:
                    user.totp_backup_codes = updated_codes
                    audit_logger.log_security_event(
                        event_type="2FA_BACKUP_CODE_USED",
                        user_id=user.id,
                        username=user.usuario,
                        ip_address=client_ip,
                        severity="WARNING"
                    )
                else:
                    audit_logger.log_login_failed(
                        username=user.usuario,
                        reason="Código 2FA inválido",
                        ip_address=client_ip
                    )
                    raise HTTPException(
                        status_code=400,
                        detail="Código de autenticación inválido"
                    )
        except HTTPException:
            raise
        except Exception as e:
            print(f"[LOGIN] Error en 2FA: {e}")
            raise HTTPException(
                status_code=500,
                detail="Error al verificar código de autenticación"
            )
    
    # ============== LOGIN EXITOSO ==============
    # Resetear rate limiter
    login_limiter.record_attempt(rate_limit_key, success=True)
    
    # Registrar login exitoso en DB
    user.record_successful_login(ip_address=client_ip)
    db.commit()
    
    # Registrar en auditoría
    audit_logger.log_login_success(
        username=user.usuario,
        user_id=user.id,
        ip_address=client_ip,
        user_agent=user_agent,
        lubricentro_id=user.lubricentro_id
    )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES)
    
    return LoginResponse(
        access_token=security.create_access_token(
            user.id, expires_delta=access_token_expires, fresh=True
        ),
        refresh_token=security.create_refresh_token(
            user.id, expires_delta=refresh_token_expires
        ),
        token_type="bearer",
        requires_2fa=False
    )


@router.post("/refresh-token", response_model=Token)
def refresh_token(
    request: Request,
    db: Session = Depends(deps.get_db),
    refresh_token: str = Depends(deps.get_refresh_token_from_header)
) -> Any:
    """
    Refresh access token using a valid refresh token.
    Implementa rotación de tokens: el refresh token anterior se invalida.
    """
    client_ip = get_client_ip(request)
    
    try:
        payload = jwt.decode(
            refresh_token, settings.SECRET_KEY, algorithms=[ALGORITHM]
        )
        
        # Verificar que no esté en blacklist
        if not verify_token_not_blacklisted(refresh_token, payload):
            audit_logger.log_security_event(
                event_type="BLACKLISTED_TOKEN_USED",
                details={"token_type": "refresh"},
                ip_address=client_ip,
                severity="WARNING"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Token inválido o revocado"
            )
        
        token_type = payload.get("type")
        if token_type != "refresh":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid token type"
            )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Could not validate credentials"
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials"
        )
    
    user = crud_user.get(db, id=int(user_id))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.activo:
        raise HTTPException(status_code=400, detail="Inactive user")
    
    # ============== ROTACIÓN DE TOKENS ==============
    # Invalidar el refresh token usado (previene reutilización)
    blacklist_token(refresh_token, payload)
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES)
    
    # Generar nuevos tokens
    new_access_token = security.create_access_token(
        user.id, expires_delta=access_token_expires, fresh=False  # No es fresh
    )
    new_refresh_token = security.create_refresh_token(
        user.id, expires_delta=refresh_token_expires
    )
    
    audit_logger.log_security_event(
        event_type="TOKEN_REFRESHED",
        user_id=user.id,
        username=user.usuario,
        ip_address=client_ip,
        severity="INFO"
    )
    
    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
    }


@router.post("/logout")
def logout(
    request: Request,
    current_user = Depends(deps.get_current_user),
    token: str = Depends(deps.reusable_oauth2)
) -> Any:
    """
    Logout - invalida el token actual agregándolo a la blacklist.
    """
    client_ip = get_client_ip(request)
    
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[ALGORITHM]
        )
        blacklist_token(token, payload)
    except JWTError:
        pass  # Token ya inválido, ignorar
    
    audit_logger.log_logout(
        user_id=current_user.id,
        username=current_user.usuario,
        ip_address=client_ip
    )
    
    return {"success": True, "message": "Sesión cerrada correctamente"}
