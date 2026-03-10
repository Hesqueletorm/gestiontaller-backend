from typing import Generator, Optional
from fastapi import Depends, HTTPException, status, Header
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core import auth as security
from app.core.config import settings
from app.db.session import SessionLocal
from app.models.user import User
from app.crud.crud_user import user as crud_user
from app.schemas.token import TokenPayload

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/login/access-token"
)

reusable_oauth2_optional = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/login/access-token",
    auto_error=False  # No lanza error si el token no está presente
)

from sqlalchemy import text
from sqlalchemy.exc import OperationalError, DatabaseError

def get_db() -> Generator:
    """
    Dependency que proporciona una sesión de base de datos.
    Solo captura excepciones específicas de conexión a BD.
    """
    db = None
    try:
        db = SessionLocal()
        # Verificar la conexión de inmediato
        db.execute(text("SELECT 1"))
        yield db
    except (OperationalError, DatabaseError) as e:
        # Solo capturar errores de conexión/operación de BD, no HTTPException ni otras
        error_msg = "(Error de decodificación)"
        try:
            error_msg = str(e)
            print(f"DEBUG DB ERROR: {error_msg}")
        except UnicodeDecodeError:
            print("DEBUG DB ERROR: Mensaje de error de Postgres con caracteres no UTF-8.")
        
        raise HTTPException(
            status_code=500,
            detail=f"Error de conexión a la base de datos: {error_msg}. Verificá PostgreSQL."
        )
    finally:
        if db:
            db.close()



def get_current_user(
    db: Session = Depends(get_db), token: str = Depends(reusable_oauth2)
) -> User:
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[security.ALGORITHM]
        )
        token_data = TokenPayload(**payload)
    except (jwt.JWTError, ValidationError) as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Could not validate credentials: {str(e)}",
        )
    
    # Convert sub to int since user.id is Integer
    if token_data.sub is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials: token missing subject",
        )
    
    try:
        user_id = int(token_data.sub)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials: invalid user id in token",
        )
    
    user = crud_user.get(db, id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.activo:
        raise HTTPException(status_code=400, detail="Inactive user")
    return user


async def get_current_user_optional(
    db: Session = Depends(get_db), token: Optional[str] = Depends(reusable_oauth2_optional)
) -> Optional[User]:
    """
    Versión opcional de get_current_user que retorna None si no hay token válido
    en lugar de lanzar una excepción. Útil para endpoints públicos/semi-públicos.
    """
    if not token:
        return None
    
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[security.ALGORITHM]
        )
        token_data = TokenPayload(**payload)
    except (jwt.JWTError, ValidationError):
        # Silenciosamente retornar None en lugar de lanzar error
        return None
    
    if token_data.sub is None:
        return None
    
    try:
        user_id = int(token_data.sub)
    except ValueError:
        return None
    
    user = crud_user.get(db, id=user_id)
    if not user or not user.activo:
        return None
    
    return user


def get_current_active_superuser(
    current_user: User = Depends(get_current_user),
) -> User:
    """Solo Desarrollador (rol=0) tiene acceso"""
    if current_user.rol != 0:
        raise HTTPException(
            status_code=403, detail="Solo el Desarrollador tiene acceso a este recurso"
        )
    return current_user


def get_current_active_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Solo Desarrollador (rol=0) o Administrador (rol=1) tienen acceso.
    Usado para gestión de usuarios del lubricentro.
    """
    if current_user.rol not in [0, 1]:
        raise HTTPException(
            status_code=403, detail="Se requiere rol de Administrador para gestionar usuarios"
        )
    if current_user.lubricentro_id is None and current_user.rol != 0:
        raise HTTPException(
            status_code=403, detail="Debés pertenecer a un lubricentro para gestionar usuarios"
        )
    return current_user


def get_current_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Desarrollador (rol=0), Administrador (rol=1) o Coordinador (rol=2) tienen acceso.
    Usado para acceso a Configuraciones.
    """
    if current_user.rol not in [0, 1, 2]:
        raise HTTPException(
            status_code=403, detail="Se requiere rol de Administrador o Coordinador"
        )
    return current_user


def get_refresh_token_from_header(authorization: Optional[str] = Header(None)) -> str:
    """
    Extract refresh token from Authorization header.
    Expected format: Bearer <refresh_token>
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Missing authorization header"
        )
    
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid authentication scheme"
            )
        return token
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid authorization header format"
        )
