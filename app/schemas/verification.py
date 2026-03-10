# Schemas para verificación de email
from typing import Optional
from pydantic import BaseModel, EmailStr


class RegisterRequest(BaseModel):
    """Datos para iniciar registro"""
    usuario: str
    email: str
    password: str
    nombre: Optional[str] = None
    
    # Multi-tenant: Opción de crear nuevo lubricentro o unirse a uno existente
    crear_lubricentro: bool = False  # True = crear nuevo, False = unirse a existente
    nombre_lubricentro: Optional[str] = None  # Solo si crear_lubricentro = True
    codigo_lubricentro: Optional[str] = None  # Solo si crear_lubricentro = False


class VerifyEmailRequest(BaseModel):
    """Datos para verificar código de email"""
    email: str
    codigo: str


class ResendCodeRequest(BaseModel):
    """Datos para reenviar código"""
    email: str


class RegisterResponse(BaseModel):
    """Respuesta del registro"""
    success: bool
    message: str
    email: Optional[str] = None


class RecuperarPasswordRequest(BaseModel):
    """Solicitar código para recuperar contraseña"""
    email: str


class VerificarCodigoRecuperacionRequest(BaseModel):
    """Verificar código de recuperación"""
    email: str
    codigo: str


class CambiarPasswordRequest(BaseModel):
    """Cambiar contraseña después de verificar código"""
    email: str
    codigo: str
    nueva_password: str
