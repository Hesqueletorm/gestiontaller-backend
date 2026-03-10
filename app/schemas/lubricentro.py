# Schemas Pydantic para Lubricentro

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel


class LubricentroBase(BaseModel):
    """Base schema para lubricentros"""
    nombre: str
    color_fondo: Optional[str] = "#04060c"
    color_tematica: Optional[str] = "#f2e71a"
    color_tematica2: Optional[str] = "#FFA000"
    color_letras: Optional[str] = "#F5F7FA"
    tema: Optional[str] = "dark"
    idioma: Optional[str] = "Español"


class LubricentroCreate(BaseModel):
    """Schema para crear un nuevo lubricentro"""
    nombre: str
    color_fondo: Optional[str] = "#04060c"
    color_tematica: Optional[str] = "#f2e71a"
    color_tematica2: Optional[str] = "#FFA000"
    color_letras: Optional[str] = "#F5F7FA"
    tema: Optional[str] = "dark"


class LubricentroUpdate(BaseModel):
    """Schema para actualizar lubricentro"""
    nombre: Optional[str] = None
    color_fondo: Optional[str] = None
    color_tematica: Optional[str] = None
    color_tematica2: Optional[str] = None
    color_letras: Optional[str] = None
    tema: Optional[str] = None
    idioma: Optional[str] = None
    activo: Optional[bool] = None


class Lubricentro(LubricentroBase):
    """Schema de respuesta de lubricentro"""
    id: int
    codigo: str
    fecha_creacion: Optional[datetime] = None
    activo: bool = True

    class Config:
        from_attributes = True


class LubricentroSimple(BaseModel):
    """Schema simplificado para listar lubricentros (en registro)"""
    id: int
    nombre: str
    codigo: str

    class Config:
        from_attributes = True


class LubricentroListResponse(BaseModel):
    """Respuesta al listar lubricentros disponibles"""
    lubricentros: List[LubricentroSimple]
