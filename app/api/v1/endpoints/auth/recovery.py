"""
Endpoints de Recuperación de Contraseña
Con seguridad mejorada: rate limiting y auditoría
"""
from datetime import timedelta, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.api import deps
from app.core import auth as security
from app.core.email import send_recovery_email
from app.crud.crud_user import user as crud_user
from app.schemas.verification import (
    RegisterResponse,
    RecuperarPasswordRequest,
    VerificarCodigoRecuperacionRequest,
    CambiarPasswordRequest
)
from .utils import (
    codigos_recuperacion,
    generar_codigo,
    limpiar_codigos_recuperacion_expirados
)

# Importar módulo de seguridad
from app.core.security.rate_limiter import password_reset_limiter
from app.core.security.audit_logger import audit_logger
from app.core.security.exceptions import RateLimitExceeded
from app.core.security.middleware import get_client_ip

router = APIRouter()


@router.post("/recuperar-password", response_model=RegisterResponse)
def solicitar_recuperacion(
    http_request: Request,
    request: RecuperarPasswordRequest,
    db: Session = Depends(deps.get_db)
) -> Any:
    """
    Solicitar código para recuperar contraseña.
    Envía un código de 6 dígitos al email del usuario.
    
    Seguridad:
    - Rate limiting por email (máx 3 solicitudes por hora)
    - Auditoría de solicitudes
    """
    # Obtener IP del cliente
    client_ip = get_client_ip(http_request)
    user_agent = http_request.headers.get("User-Agent", "")
    
    # Rate limiting por email (para evitar spam a un usuario específico)
    rate_key = f"{request.email}:{client_ip}"
    if not password_reset_limiter.is_allowed(rate_key):
        retry_after = password_reset_limiter.get_retry_after(rate_key)
        audit_logger.log_rate_limit_exceeded(
            identifier=request.email,
            limiter_name="password_reset",
            ip_address=client_ip
        )
        raise RateLimitExceeded(retry_after=retry_after)
    
    limpiar_codigos_recuperacion_expirados()
    
    # Verificar si el email existe
    user = crud_user.get_by_email(db, email=request.email)
    
    # Registrar el intento siempre (para rate limiting)
    password_reset_limiter.record_attempt(rate_key, success=True)
    
    if not user:
        # Por seguridad, no revelamos si el email existe o no
        # Pero simulamos éxito igual y auditamos
        audit_logger.log_password_reset_request(
            email=request.email,
            user_id=None,
            ip_address=client_ip,
            user_agent=user_agent,
            success=False,
            reason="Email no encontrado"
        )
        # Respondemos igual para no revelar información
        return RegisterResponse(
            success=True,
            message="Si el email está registrado, recibirás un código de verificación.",
            email=request.email
        )
    
    # Generar código
    codigo = generar_codigo()
    
    # Enviar email
    exito, mensaje = send_recovery_email(request.email, codigo)
    
    if not exito:
        audit_logger.log_password_reset_request(
            email=request.email,
            user_id=user.id,
            ip_address=client_ip,
            success=False,
            reason=f"Error de envío: {mensaje}"
        )
        raise HTTPException(
            status_code=500,
            detail=f"Error al enviar código: {mensaje}"
        )
    
    # Guardar código temporalmente
    codigos_recuperacion[request.email] = {
        'codigo': codigo,
        'timestamp': datetime.now(),
        'user_id': user.id,
        'verificado': False,
        'ip_address': client_ip  # Guardar IP para auditoría
    }
    
    # Auditar solicitud exitosa
    audit_logger.log_password_reset_request(
        email=request.email,
        user_id=user.id,
        ip_address=client_ip,
        user_agent=user_agent,
        success=True
    )
    
    return RegisterResponse(
        success=True,
        message="Código enviado a tu email",
        email=request.email
    )


@router.post("/verificar-codigo-recuperacion", response_model=RegisterResponse)
def verificar_codigo_recuperacion(
    request: VerificarCodigoRecuperacionRequest,
    db: Session = Depends(deps.get_db)
) -> Any:
    """
    Verificar código de recuperación.
    Si es correcto, marca el código como verificado para permitir cambio de contraseña.
    """
    limpiar_codigos_recuperacion_expirados()
    
    # Verificar si hay código pendiente
    if request.email not in codigos_recuperacion:
        raise HTTPException(
            status_code=400,
            detail="No hay solicitud de recuperación pendiente para este email."
        )
    
    datos = codigos_recuperacion[request.email]
    
    # Verificar si expiró
    if (datetime.now() - datos['timestamp']) > timedelta(minutes=10):
        del codigos_recuperacion[request.email]
        raise HTTPException(
            status_code=400,
            detail="El código ha expirado. Solicitá uno nuevo."
        )
    
    # Verificar código
    if datos['codigo'] != request.codigo:
        raise HTTPException(
            status_code=400,
            detail="Código incorrecto"
        )
    
    # Marcar como verificado (no eliminar aún, se necesita para cambiar password)
    codigos_recuperacion[request.email]['verificado'] = True
    
    return RegisterResponse(
        success=True,
        message="Código verificado. Podés cambiar tu contraseña.",
        email=request.email
    )


@router.post("/cambiar-password", response_model=RegisterResponse)
def cambiar_password(
    http_request: Request,
    request: CambiarPasswordRequest,
    db: Session = Depends(deps.get_db)
) -> Any:
    """
    Cambiar contraseña después de verificar el código.
    
    Seguridad:
    - Auditoría de cambios de contraseña
    - Validación de fortaleza de contraseña
    """
    # Obtener IP del cliente
    client_ip = get_client_ip(http_request)
    user_agent = http_request.headers.get("User-Agent", "")
    
    limpiar_codigos_recuperacion_expirados()
    
    # Verificar si hay código verificado
    if request.email not in codigos_recuperacion:
        audit_logger.log_password_change(
            user_id=None,
            username=request.email,
            ip_address=client_ip,
            success=False,
            reason="No hay solicitud pendiente"
        )
        raise HTTPException(
            status_code=400,
            detail="No hay solicitud de recuperación pendiente."
        )
    
    datos = codigos_recuperacion[request.email]
    
    # Verificar que el código fue verificado
    if not datos.get('verificado'):
        raise HTTPException(
            status_code=400,
            detail="Primero debés verificar el código."
        )
    
    # Verificar que sea el mismo código
    if datos['codigo'] != request.codigo:
        raise HTTPException(
            status_code=400,
            detail="Código inválido."
        )
    
    # Validar nueva contraseña
    if len(request.nueva_password) < 6:
        raise HTTPException(
            status_code=400,
            detail="La contraseña debe tener al menos 6 caracteres."
        )
    
    # Obtener usuario y actualizar contraseña
    user = crud_user.get(db, id=datos['user_id'])
    if not user:
        audit_logger.log_password_change(
            user_id=datos['user_id'],
            username=request.email,
            ip_address=client_ip,
            success=False,
            reason="Usuario no encontrado"
        )
        raise HTTPException(
            status_code=400,
            detail="Usuario no encontrado."
        )
    
    # Actualizar contraseña
    hashed_password = security.get_password_hash(request.nueva_password)
    user.hashed_password = hashed_password
    db.add(user)
    db.commit()
    
    # Auditar cambio exitoso
    audit_logger.log_password_change(
        user_id=user.id,
        username=user.usuario,
        ip_address=client_ip,
        user_agent=user_agent,
        success=True
    )
    
    # Limpiar código usado
    del codigos_recuperacion[request.email]
    
    return RegisterResponse(
        success=True,
        message="¡Contraseña actualizada exitosamente!",
        email=request.email
    )
