"""
Schemas locales para el módulo de Clientes
"""
from typing import List, Optional
from pydantic import BaseModel

from app.schemas.client_schema import Client


# Schema para respuesta paginada
class ClientListResponse(BaseModel):
    items: List[Client]
    total: int
    page: int
    page_size: int
    total_pages: int

    class Config:
        from_attributes = True


# Schema para actualizar km de vehículos
class VehicleKmUpdate(BaseModel):
    descripcion: str
    km: Optional[float] = None


# Schemas para validación de unicidad
class ValidateClientData(BaseModel):
    email: Optional[str] = None
    patentes: Optional[List[str]] = None
    cliente_id: Optional[int] = None  # ID del cliente seleccionado (si existe)
    cliente_nombre: Optional[str] = None  # Nombre del cliente ingresado


class ConflictDetail(BaseModel):
    tipo: str  # "email" o "patente"
    valor: str
    cliente_existente: str
    cliente_id: int


class ValidateResponse(BaseModel):
    valid: bool
    conflicts: List[ConflictDetail] = []
    message: Optional[str] = None
