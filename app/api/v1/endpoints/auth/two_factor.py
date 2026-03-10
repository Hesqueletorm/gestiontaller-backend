"""
Endpoints para Autenticación de Dos Factores (2FA/TOTP)
"""
from typing import Any, Optional
import json
import qrcode
import io
import base64

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.api import deps
from app.models.user import User
from app.core.config import settings
from app.core.security.totp import (
    totp_manager, 
    encrypt_totp_secret, 
    decrypt_totp_secret
)
from app.core.security.audit_logger import audit_logger


router = APIRouter()


# ============== SCHEMAS ==============

class Enable2FAResponse(BaseModel):
    """Respuesta al habilitar 2FA"""
    secret: str
    qr_code: str  # Base64 de la imagen QR
    backup_codes: list[str]
    message: str


class Verify2FARequest(BaseModel):
    """Request para verificar código 2FA"""
    code: str


class Disable2FARequest(BaseModel):
    """Request para deshabilitar 2FA"""
    code: str  # Código TOTP o backup code para confirmar
    password: str  # Contraseña para doble verificación


class TwoFAStatusResponse(BaseModel):
    """Estado de 2FA del usuario"""
    enabled: bool
    backup_codes_remaining: int


# ============== ENDPOINTS ==============

@router.get("/status", response_model=TwoFAStatusResponse)
def get_2fa_status(
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db)
) -> Any:
    """
    Obtener estado de 2FA del usuario actual.
    """
    backup_count = 0
    if current_user.totp_backup_codes:
        try:
            codes = json.loads(current_user.totp_backup_codes)
            backup_count = len(codes)
        except json.JSONDecodeError:
            pass
    
    return TwoFAStatusResponse(
        enabled=current_user.totp_enabled or False,
        backup_codes_remaining=backup_count
    )


@router.post("/enable", response_model=Enable2FAResponse)
def enable_2fa(
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db)
) -> Any:
    """
    Habilitar 2FA para el usuario actual.
    Genera secreto TOTP, QR code y códigos de backup.
    
    IMPORTANTE: El usuario debe verificar el código antes de que 2FA esté activo.
    """
    if current_user.totp_enabled:
        raise HTTPException(
            status_code=400,
            detail="2FA ya está habilitado para esta cuenta"
        )
    
    # Generar secreto y URI
    email = current_user.email or f"{current_user.usuario}@gestiondetaller.local"
    secret, uri = totp_manager.generate_secret(email, issuer="GestionDeTaller")
    
    # Generar QR code como base64
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(uri)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")
    
    # Convertir a base64
    buffer = io.BytesIO()
    qr_img.save(buffer, format="PNG")
    qr_base64 = base64.b64encode(buffer.getvalue()).decode()
    
    # Generar códigos de backup
    backup_codes = totp_manager.generate_backup_codes(10)
    
    # Guardar temporalmente (sin activar aún)
    # El secreto se encripta antes de guardar
    encrypted_secret = encrypt_totp_secret(secret, settings.SECRET_KEY)
    current_user.totp_secret = encrypted_secret
    current_user.totp_backup_codes = json.dumps(backup_codes)
    # NO activar aún - esperar verificación
    current_user.totp_enabled = False
    
    db.commit()
    
    audit_logger.log_security_event(
        event_type="2FA_SETUP_INITIATED",
        user_id=current_user.id,
        username=current_user.usuario,
        details={"email": email},
        severity="INFO"
    )
    
    return Enable2FAResponse(
        secret=secret,  # Mostrar al usuario para entrada manual
        qr_code=f"data:image/png;base64,{qr_base64}",
        backup_codes=backup_codes,
        message="Escanea el código QR con tu app de autenticación y verifica con un código"
    )


@router.post("/verify-setup")
def verify_2fa_setup(
    request: Verify2FARequest,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db)
) -> Any:
    """
    Verificar código TOTP para completar la configuración de 2FA.
    Este paso activa 2FA para la cuenta.
    """
    if current_user.totp_enabled:
        raise HTTPException(
            status_code=400,
            detail="2FA ya está activo"
        )
    
    if not current_user.totp_secret:
        raise HTTPException(
            status_code=400,
            detail="Primero debes iniciar la configuración de 2FA"
        )
    
    # Desencriptar secreto
    try:
        secret = decrypt_totp_secret(current_user.totp_secret, settings.SECRET_KEY)
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Error al procesar la configuración de 2FA"
        )
    
    # Verificar código
    if not totp_manager.verify_code(secret, request.code):
        audit_logger.log_security_event(
            event_type="2FA_SETUP_FAILED",
            user_id=current_user.id,
            username=current_user.usuario,
            details={"reason": "Código inválido"},
            severity="WARNING"
        )
        raise HTTPException(
            status_code=400,
            detail="Código inválido. Asegúrate de que tu app esté sincronizada."
        )
    
    # Activar 2FA
    current_user.totp_enabled = True
    db.commit()
    
    audit_logger.log_security_event(
        event_type="2FA_ENABLED",
        user_id=current_user.id,
        username=current_user.usuario,
        severity="INFO"
    )
    
    return {"success": True, "message": "2FA habilitado exitosamente"}


@router.post("/disable")
def disable_2fa(
    request: Disable2FARequest,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db)
) -> Any:
    """
    Deshabilitar 2FA para el usuario actual.
    Requiere código TOTP/backup y contraseña.
    """
    from app.core.auth import verify_password
    
    if not current_user.totp_enabled:
        raise HTTPException(
            status_code=400,
            detail="2FA no está habilitado"
        )
    
    # Verificar contraseña
    if not verify_password(request.password, current_user.password):
        audit_logger.log_security_event(
            event_type="2FA_DISABLE_FAILED",
            user_id=current_user.id,
            username=current_user.usuario,
            details={"reason": "Contraseña incorrecta"},
            severity="WARNING"
        )
        raise HTTPException(
            status_code=400,
            detail="Contraseña incorrecta"
        )
    
    # Verificar código TOTP o backup
    secret = decrypt_totp_secret(current_user.totp_secret, settings.SECRET_KEY)
    code_valid = totp_manager.verify_code(secret, request.code)
    
    if not code_valid:
        # Intentar con backup code
        valid, updated_codes = totp_manager.verify_backup_code(
            current_user.totp_backup_codes, 
            request.code
        )
        if not valid:
            raise HTTPException(
                status_code=400,
                detail="Código inválido"
            )
    
    # Deshabilitar 2FA
    current_user.totp_enabled = False
    current_user.totp_secret = None
    current_user.totp_backup_codes = None
    db.commit()
    
    audit_logger.log_security_event(
        event_type="2FA_DISABLED",
        user_id=current_user.id,
        username=current_user.usuario,
        severity="WARNING"
    )
    
    return {"success": True, "message": "2FA deshabilitado"}


@router.post("/regenerate-backup-codes")
def regenerate_backup_codes(
    request: Verify2FARequest,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db)
) -> Any:
    """
    Regenerar códigos de backup (invalida los anteriores).
    Requiere código TOTP para confirmar.
    """
    if not current_user.totp_enabled:
        raise HTTPException(
            status_code=400,
            detail="2FA no está habilitado"
        )
    
    # Verificar código
    secret = decrypt_totp_secret(current_user.totp_secret, settings.SECRET_KEY)
    if not totp_manager.verify_code(secret, request.code):
        raise HTTPException(
            status_code=400,
            detail="Código inválido"
        )
    
    # Generar nuevos códigos
    new_codes = totp_manager.generate_backup_codes(10)
    current_user.totp_backup_codes = json.dumps(new_codes)
    db.commit()
    
    audit_logger.log_security_event(
        event_type="2FA_BACKUP_CODES_REGENERATED",
        user_id=current_user.id,
        username=current_user.usuario,
        severity="INFO"
    )
    
    return {
        "success": True,
        "backup_codes": new_codes,
        "message": "Códigos de backup regenerados. Guárdalos en un lugar seguro."
    }
