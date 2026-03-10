# Schemas Pydantic para ProductLote (Lotes de productos)

from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ProductLoteBase(BaseModel):
    """Campos comunes para lotes"""
    producto_id: int
    cantidad: float
    fecha_vencimiento: Optional[str] = None  # Formato YYYY-MM-DD


class ProductLoteCreate(ProductLoteBase):
    """Schema para crear un lote"""
    compra_id: Optional[int] = None


class ProductLoteUpdate(BaseModel):
    """Schema para actualizar un lote"""
    cantidad: Optional[float] = None
    fecha_vencimiento: Optional[str] = None


class ProductLote(ProductLoteBase):
    """Schema de respuesta para lotes"""
    id: int
    lubricentro_id: int
    fecha_ingreso: datetime
    compra_id: Optional[int] = None
    
    # Campos calculados para el frontend
    estado_vencimiento: Optional[str] = None  # ok, warning, expired
    dias_restantes: Optional[int] = None
    texto_vencimiento: Optional[str] = None
    
    class Config:
        from_attributes = True


class ProductLoteListResponse(BaseModel):
    """Respuesta paginada de lotes"""
    items: list[ProductLote]
    total: int
