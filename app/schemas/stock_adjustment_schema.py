# Esquemas Pydantic para Ajustes de Stock
from typing import List, Optional
from enum import Enum
from pydantic import BaseModel, Field
from datetime import datetime


class TipoAjuste(str, Enum):
    """Tipos de ajuste de stock disponibles"""
    VENCIMIENTO = "vencimiento"
    DESCARTE = "descarte"
    CONSUMO_INTERNO = "consumo_interno"


class StockAdjustmentBase(BaseModel):
    """Base para ajustes de stock"""
    producto_id: int = Field(..., description="ID del producto a ajustar")
    tipo_ajuste: TipoAjuste = Field(..., description="Tipo de ajuste")
    cantidad: float = Field(..., gt=0, description="Cantidad a restar (debe ser positiva)")
    motivo: Optional[str] = Field(None, max_length=500, description="Motivo del ajuste")


class StockAdjustmentCreate(StockAdjustmentBase):
    """Esquema para crear un ajuste"""
    pass


class StockAdjustmentUpdate(BaseModel):
    """Esquema para actualizar un ajuste (solo motivo)"""
    motivo: Optional[str] = None


class StockAdjustment(StockAdjustmentBase):
    """Esquema de respuesta con datos completos"""
    id: int
    lubricentro_id: int
    fecha: datetime
    created_by: Optional[int] = None
    # Datos del producto para mostrar en UI
    producto_nombre: Optional[str] = None
    producto_codigo: Optional[str] = None

    class Config:
        from_attributes = True


class StockAdjustmentListResponse(BaseModel):
    """Respuesta paginada de ajustes"""
    items: List[StockAdjustment]
    total: int
    page: int
    page_size: int
    total_pages: int


class StockAdjustmentStats(BaseModel):
    """Estadísticas de ajustes por tipo"""
    total_vencimiento: int = 0
    total_descarte: int = 0
    total_consumo_interno: int = 0
    cantidad_vencimiento: float = 0.0
    cantidad_descarte: float = 0.0
    cantidad_consumo_interno: float = 0.0
