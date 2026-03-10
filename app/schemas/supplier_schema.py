# Schemas Pydantic para Proveedores
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime


class SupplierBase(BaseModel):
    """Schema base para proveedores"""
    nombre: str
    cuit: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[str] = None
    direccion: Optional[str] = None
    contacto: Optional[str] = None
    rubro: Optional[str] = None
    notas: Optional[str] = None


class SupplierCreate(SupplierBase):
    """Schema para crear un proveedor"""
    pass


class SupplierUpdate(BaseModel):
    """Schema para actualizar un proveedor"""
    nombre: Optional[str] = None
    cuit: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[str] = None
    direccion: Optional[str] = None
    contacto: Optional[str] = None
    rubro: Optional[str] = None
    notas: Optional[str] = None
    activo: Optional[bool] = None


class SupplierResponse(SupplierBase):
    """Schema de respuesta para un proveedor"""
    id: int
    activo: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SupplierListResponse(BaseModel):
    """Schema para lista de proveedores"""
    items: List[SupplierResponse]
    total: int
    page: int
    page_size: int


class SupplierSimple(BaseModel):
    """Schema simplificado para autocompletado"""
    id: int
    nombre: str
    cuit: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[str] = None

    class Config:
        from_attributes = True
