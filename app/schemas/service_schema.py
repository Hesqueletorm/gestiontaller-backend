# Schemas Pydantic para Servicios

from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ServiceBase(BaseModel):
    codigo: Optional[str] = None
    nombre: str
    descripcion: Optional[str] = None
    precio: float = 0
    categoria: Optional[str] = None
    activo: int = 1


class ServiceCreate(ServiceBase):
    pass


class ServiceUpdate(BaseModel):
    codigo: Optional[str] = None
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    precio: Optional[float] = None
    categoria: Optional[str] = None
    activo: Optional[int] = None


class Service(ServiceBase):
    id: int
    lubricentro_id: Optional[int] = None
    fecha_creacion: Optional[datetime] = None

    class Config:
        from_attributes = True


# Alias en español
ServicioBase = ServiceBase
ServicioCreate = ServiceCreate
ServicioUpdate = ServiceUpdate
Servicio = Service
