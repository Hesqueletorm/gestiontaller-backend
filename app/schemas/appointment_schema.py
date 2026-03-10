# Schemas Pydantic para Turnos (Appointments)
# Compatible con el modelo de lubricentroM

from typing import Optional
from pydantic import BaseModel


class AppointmentBase(BaseModel):
    """Base schema para turnos"""
    fecha: str  # Formato YYYY-MM-DD
    hora: str   # Formato HH:MM
    cliente: str
    vehiculo: Optional[str] = ""
    servicio: Optional[str] = ""
    notas: Optional[str] = ""
    duracion: int = 30  # Minutos
    cliente_id: Optional[int] = None  # ID del cliente asociado (opcional)


class AppointmentCreate(AppointmentBase):
    """Schema para crear un turno"""
    pass


class AppointmentUpdate(BaseModel):
    """Schema para actualizar un turno"""
    fecha: Optional[str] = None
    hora: Optional[str] = None
    cliente: Optional[str] = None
    vehiculo: Optional[str] = None
    servicio: Optional[str] = None
    notas: Optional[str] = None
    duracion: Optional[int] = None
    cliente_id: Optional[int] = None


class Appointment(AppointmentBase):
    """Schema de respuesta de turno"""
    id: int
    lubricentro_id: Optional[int] = None
    cliente_nombre: Optional[str] = None  # Nombre del cliente si está asociado
    
    class Config:
        from_attributes = True
