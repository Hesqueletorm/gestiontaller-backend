from typing import Any, List, Dict
from datetime import datetime, timedelta
import random
import string
import os
import uuid
import shutil
from fastapi import APIRouter, Body, Depends, HTTPException, UploadFile, File
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.api import deps
from app.crud.crud_user import user as crud_user
from app.schemas.user import User, UserCreate, UserUpdate
from app.models.user import User as UserModel
from app.core.email import send_recovery_email
from app.core.auth import verify_password, get_password_hash

router = APIRouter()

# Directorio para fotos de perfil
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))), "uploads", "avatars")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Almacenamiento temporal de códigos para cambio de contraseña
_password_change_codes: Dict[str, Dict[str, Any]] = {}


def _generar_codigo() -> str:
    """Genera un código de 6 dígitos"""
    return ''.join(random.choices(string.digits, k=6))


def _limpiar_codigos_expirados():
    """Limpia códigos que hayan expirado (>10 minutos)"""
    ahora = datetime.now()
    emails_a_eliminar = [
        email for email, datos in _password_change_codes.items()
        if (ahora - datos['timestamp']) > timedelta(minutes=10)
    ]
    for email in emails_a_eliminar:
        del _password_change_codes[email]

@router.get("/", response_model=List[User])
def read_users(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_active_superuser),
) -> Any:
    users = crud_user.get_multi(db, skip=skip, limit=limit)
    return users

@router.post("/", response_model=User)
def create_user(
    *,
    db: Session = Depends(deps.get_db),
    user_in: UserCreate,
    # Open registration or protected? Let's keep it open or protected depending on requirements. 
    # For now, allow open registration or at least admin based.
    # If we want open registration, remove current_user depend.
) -> Any:
    user = crud_user.get_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this username already exists in the system.",
        )
    user = crud_user.create(db, obj_in=user_in)
    return user

@router.get("/me", response_model=User)
def read_user_me(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    # Agregar el nombre del lubricentro al usuario
    user_data = {
        "id": current_user.id,
        "usuario": current_user.usuario,
        "email": current_user.email,
        "nombre": current_user.nombre,
        "activo": current_user.activo,
        "rol": current_user.rol,
        "imagen": current_user.imagen,
        "lubricentro_id": current_user.lubricentro_id,
        "fecha_creacion": current_user.fecha_creacion,
        "email_verificado": current_user.email_verificado,
        "color_fondo": current_user.color_fondo,
        "color_tematica": current_user.color_tematica,
        "color_tematica2": current_user.color_tematica2,
        "color_letras": current_user.color_letras,
        "tema": current_user.tema,
        "idioma": current_user.idioma,
        "lubricentro_nombre": current_user.lubricentro.nombre if current_user.lubricentro else None,
        "lubricentro_codigo": current_user.lubricentro.codigo if current_user.lubricentro else None,
    }
    return user_data


class UserUpdateMe(BaseModel):
    usuario: str | None = None
    email: str | None = None
    nombre: str | None = None


class PasswordChange(BaseModel):
    current_password: str
    new_password: str


class PasswordChangeByCode(BaseModel):
    codigo: str
    new_password: str


class RequestPasswordCodeResponse(BaseModel):
    success: bool
    message: str


@router.put("/me", response_model=User)
def update_user_me(
    *,
    db: Session = Depends(deps.get_db),
    user_in: UserUpdateMe,
    current_user: UserModel = Depends(deps.get_current_user),
) -> Any:
    """
    Actualizar datos del usuario actual.
    """
    update_data = user_in.model_dump(exclude_unset=True)
    
    # Verificar si el usuario ya existe (si se está cambiando)
    if "usuario" in update_data and update_data["usuario"]:
        existing = db.query(UserModel).filter(
            UserModel.usuario == update_data["usuario"],
            UserModel.id != current_user.id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Ese nombre de usuario ya está en uso")
    
    # Verificar si el email ya existe (si se está cambiando)
    if "email" in update_data and update_data["email"]:
        existing = db.query(UserModel).filter(
            UserModel.email == update_data["email"],
            UserModel.id != current_user.id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Ese email ya está en uso")
    
    for field, value in update_data.items():
        if hasattr(current_user, field) and value is not None:
            setattr(current_user, field, value)
    
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return current_user


@router.put("/me/password")
def change_password(
    *,
    db: Session = Depends(deps.get_db),
    password_data: PasswordChange,
    current_user: UserModel = Depends(deps.get_current_user),
) -> Any:
    """
    Cambiar contraseña del usuario actual.
    """
    # Verificar contraseña actual usando passlib
    if not verify_password(password_data.current_password, current_user.password):
        raise HTTPException(status_code=400, detail="La contraseña actual es incorrecta")
    
    # Actualizar con nueva contraseña usando passlib
    current_user.password = get_password_hash(password_data.new_password)
    
    db.add(current_user)
    db.commit()
    
    return {"message": "Contraseña actualizada correctamente"}


@router.post("/me/request-password-code", response_model=RequestPasswordCodeResponse)
def request_password_change_code(
    db: Session = Depends(deps.get_db),
    current_user: UserModel = Depends(deps.get_current_user),
) -> Any:
    """
    Solicitar código por email para cambiar contraseña.
    Alternativa a usar la contraseña actual.
    """
    _limpiar_codigos_expirados()
    
    if not current_user.email:
        raise HTTPException(
            status_code=400, 
            detail="Tu cuenta no tiene email asociado. Usa tu contraseña actual."
        )
    
    # Generar código
    codigo = _generar_codigo()
    
    # Enviar email
    exito, mensaje = send_recovery_email(current_user.email, codigo)
    
    if not exito:
        raise HTTPException(
            status_code=500,
            detail=f"Error al enviar código: {mensaje}"
        )
    
    # Guardar código
    _password_change_codes[current_user.email] = {
        'codigo': codigo,
        'timestamp': datetime.now(),
        'user_id': current_user.id,
        'verificado': False
    }
    
    return RequestPasswordCodeResponse(
        success=True,
        message=f"Código enviado a {current_user.email}"
    )


@router.put("/me/password-by-code")
def change_password_by_code(
    *,
    db: Session = Depends(deps.get_db),
    password_data: PasswordChangeByCode,
    current_user: UserModel = Depends(deps.get_current_user),
) -> Any:
    """
    Cambiar contraseña usando código enviado por email.
    """
    _limpiar_codigos_expirados()
    
    if not current_user.email:
        raise HTTPException(status_code=400, detail="Tu cuenta no tiene email asociado")
    
    # Verificar si hay código pendiente
    if current_user.email not in _password_change_codes:
        raise HTTPException(
            status_code=400,
            detail="No hay código pendiente. Solicita uno nuevo."
        )
    
    datos = _password_change_codes[current_user.email]
    
    # Verificar que es del mismo usuario
    if datos['user_id'] != current_user.id:
        raise HTTPException(status_code=400, detail="Código inválido")
    
    # Verificar si expiró
    if (datetime.now() - datos['timestamp']) > timedelta(minutes=10):
        del _password_change_codes[current_user.email]
        raise HTTPException(
            status_code=400,
            detail="El código ha expirado. Solicita uno nuevo."
        )
    
    # Verificar código
    if datos['codigo'] != password_data.codigo:
        raise HTTPException(status_code=400, detail="Código incorrecto")
    
    # Validar nueva contraseña
    if len(password_data.new_password) < 6:
        raise HTTPException(
            status_code=400,
            detail="La contraseña debe tener al menos 6 caracteres"
        )
    
    # Actualizar contraseña usando passlib
    current_user.password = get_password_hash(password_data.new_password)
    
    db.add(current_user)
    db.commit()
    
    # Limpiar código usado
    del _password_change_codes[current_user.email]
    
    return {"message": "Contraseña actualizada correctamente"}


@router.post("/me/avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    db: Session = Depends(deps.get_db),
    current_user: UserModel = Depends(deps.get_current_user),
) -> Any:
    """
    Subir o actualizar foto de perfil del usuario actual.
    Acepta archivos JPG, PNG, WebP, GIF o BMP de hasta 5MB.
    """
    # Validar tipo de archivo (incluir formatos comunes)
    allowed_types = [
        "image/jpeg", "image/png", "image/webp", "image/jpg",
        "image/gif", "image/bmp", "image/x-ms-bmp",
        "application/octet-stream"  # Para blobs de cámara
    ]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Tipo de archivo no permitido ({file.content_type}). Usa JPG, PNG, WebP, GIF o BMP."
        )
    
    # Validar tamaño (5MB máximo)
    contents = await file.read()
    if len(contents) > 5 * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail="El archivo es demasiado grande. Máximo 5MB."
        )
    
    # Eliminar avatar anterior si existe
    if current_user.imagen:
        old_path = os.path.join(UPLOAD_DIR, os.path.basename(current_user.imagen))
        if os.path.exists(old_path):
            try:
                os.remove(old_path)
            except Exception:
                pass
    
    # Generar nombre único
    extension = file.filename.split(".")[-1] if "." in file.filename else "jpg"
    filename = f"{current_user.id}_{uuid.uuid4().hex[:8]}.{extension}"
    filepath = os.path.join(UPLOAD_DIR, filename)
    
    # Guardar archivo
    with open(filepath, "wb") as f:
        f.write(contents)
    
    # Actualizar usuario con la URL de la imagen
    current_user.imagen = f"/uploads/avatars/{filename}"
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    
    return {
        "success": True,
        "message": "Foto de perfil actualizada",
        "imagen": current_user.imagen
    }


@router.delete("/me/avatar")
def delete_avatar(
    db: Session = Depends(deps.get_db),
    current_user: UserModel = Depends(deps.get_current_user),
) -> Any:
    """
    Eliminar foto de perfil del usuario actual.
    """
    if current_user.imagen:
        # Eliminar archivo
        old_path = os.path.join(UPLOAD_DIR, os.path.basename(current_user.imagen))
        if os.path.exists(old_path):
            try:
                os.remove(old_path)
            except Exception:
                pass
        
        # Limpiar campo en DB
        current_user.imagen = None
        db.add(current_user)
        db.commit()
    
    return {"success": True, "message": "Foto de perfil eliminada"}
