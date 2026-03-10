# Schemas Pydantic para User
# Sistema de roles: 0=Desarrollador, 1=Administrador, 2=Coordinador, 3=Operador

from typing import Optional, List
from datetime import datetime
from enum import IntEnum
from pydantic import BaseModel, EmailStr


class RolUsuario(IntEnum):
    """Enum con los roles del sistema"""
    DESARROLLADOR = 0  # Solo usuario 'admin', acceso total
    ADMINISTRADOR = 1  # Dueño del lubricentro
    COORDINADOR = 2    # Supervisor, sin gestión de usuarios
    OPERADOR = 3       # Empleado básico


class UserBase(BaseModel):
    """Base schema para usuarios"""
    usuario: Optional[str] = None
    email: Optional[str] = None
    nombre: Optional[str] = None
    activo: Optional[bool] = True
    rol: Optional[int] = RolUsuario.OPERADOR  # Por defecto Operador
    imagen: Optional[str] = None
    lubricentro_id: Optional[int] = None
    # Configuración visual (puede sobreescribir la del lubricentro)
    color_fondo: Optional[str] = None
    color_tematica: Optional[str] = None
    color_tematica2: Optional[str] = None
    color_letras: Optional[str] = None
    tema: Optional[str] = None
    idioma: Optional[str] = None


class UserCreate(BaseModel):
    """Schema para crear un nuevo usuario"""
    usuario: str
    email: str
    password: str
    nombre: Optional[str] = None
    lubricentro_id: Optional[int] = None
    rol: Optional[int] = RolUsuario.OPERADOR
    aprobado: Optional[bool] = True  # False si necesita aprobación del admin


class UserUpdate(BaseModel):
    """Schema para actualizar usuario"""
    email: Optional[str] = None
    nombre: Optional[str] = None
    password: Optional[str] = None
    activo: Optional[bool] = None
    rol: Optional[int] = None
    imagen: Optional[str] = None


class UserAdminUpdate(BaseModel):
    """
    Schema para que el Administrador actualice usuarios de su lubricentro.
    Solo puede asignar roles Coordinador (2) o Operador (3).
    """
    rol: Optional[int] = None
    activo: Optional[bool] = None
    nombre: Optional[str] = None


class UserConfigUpdate(BaseModel):
    """Schema para actualizar configuración visual del usuario"""
    color_fondo: Optional[str] = None
    color_tematica: Optional[str] = None
    color_tematica2: Optional[str] = None
    color_letras: Optional[str] = None
    tema: Optional[str] = None
    idioma: Optional[str] = None
    nombre_lubricentro: Optional[str] = None  # Para actualizar nombre del lubricentro
    # Colores de la barra de identidad (gradiente 3 colores)
    color_identidad1: Optional[str] = None
    color_identidad2: Optional[str] = None
    color_identidad3: Optional[str] = None
    # Pesos (espacio/tamaño) de cada color
    peso_identidad1: Optional[int] = None
    peso_identidad2: Optional[int] = None
    peso_identidad3: Optional[int] = None


class UserConfig(BaseModel):
    """Schema de respuesta de configuración del usuario"""
    lubricentro_id: Optional[int] = None
    lubricentro_nombre: Optional[str] = None
    lubricentro_codigo: Optional[str] = None
    color_fondo: str = "#04060c"
    color_tematica: str = "#f2e71a"
    color_tematica2: str = "#FFA000"
    color_letras: str = "#F5F7FA"
    tema: str = "dark"
    idioma: str = "Español"
    # Colores de la barra de identidad (gradiente 3 colores)
    color_identidad1: str = "#FFA000"
    color_identidad2: str = "#FBF7E3"
    color_identidad3: str = "#0F172A"
    # Pesos (espacio/tamaño) de cada color
    peso_identidad1: int = 33
    peso_identidad2: int = 34
    peso_identidad3: int = 33

    class Config:
        from_attributes = True


class UserInDBBase(UserBase):
    """Schema base para usuario en DB"""
    id: Optional[int] = None
    fecha_creacion: Optional[datetime] = None
    email_verificado: Optional[bool] = True

    class Config:
        from_attributes = True  # Pydantic v2


class User(UserInDBBase):
    """Schema de respuesta de usuario (sin password)"""
    lubricentro_nombre: Optional[str] = None  # Nombre del lubricentro (join)
    lubricentro_codigo: Optional[str] = None  # Código del lubricentro (join)
    rol_nombre: Optional[str] = None  # Nombre del rol (para mostrar en UI)


class UserInDB(UserInDBBase):
    """Schema interno con password hasheado"""
    password: str


class UserListItem(BaseModel):
    """Schema simplificado para lista de usuarios"""
    id: int
    usuario: str
    email: Optional[str] = None
    nombre: Optional[str] = None
    rol: int
    rol_nombre: str
    activo: bool
    aprobado: bool = True  # False si está pendiente de aprobación
    fecha_creacion: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    """Respuesta de lista de usuarios del lubricentro"""
    usuarios: List[UserListItem]
    total: int
