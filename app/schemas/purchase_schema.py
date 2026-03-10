# Schemas Pydantic para Compras
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime


# --- Purchase Items ---
class PurchaseItemBase(BaseModel):
    articulo: str
    codigo: Optional[str] = None
    cantidad: float
    precio_unitario: float
    iva_porcentaje: float = 21.0


class PurchaseItemCreate(PurchaseItemBase):
    producto_id: Optional[int] = None  # ID del producto en stock (opcional)
    fecha_vencimiento: Optional[str] = None  # Fecha vencimiento formato YYYY-MM-DD


class PurchaseItem(PurchaseItemBase):
    id: int
    compra_id: int
    producto_id: Optional[int] = None
    subtotal: float
    total: float

    class Config:
        from_attributes = True


# --- Purchases ---
class PurchaseCreate(BaseModel):
    """Schema para crear una nueva compra"""
    fecha: Optional[datetime] = None  # Si es None, se usa fecha actual
    numero_factura: Optional[str] = None
    
    # Datos del proveedor
    proveedor_nombre: str
    proveedor_cuit: Optional[str] = None
    proveedor_telefono: Optional[str] = None
    proveedor_email: Optional[str] = None
    
    # Método de pago
    metodo_pago: str = "Efectivo"
    
    # Observaciones
    observaciones: Optional[str] = None
    
    # Items de la compra
    items: List[PurchaseItemCreate] = []


class PurchaseBase(BaseModel):
    """Schema base para lectura de compras"""
    id: int
    fecha: datetime
    numero_factura: Optional[str] = None
    proveedor_nombre: str
    metodo_pago: str
    subtotal: float
    iva: float
    total: float

    class Config:
        from_attributes = True


class Purchase(PurchaseBase):
    """Schema de compra con todos los detalles"""
    proveedor_cuit: Optional[str] = None
    proveedor_telefono: Optional[str] = None
    proveedor_email: Optional[str] = None
    observaciones: Optional[str] = None
    created_at: Optional[datetime] = None
    items: List[PurchaseItem] = []


class PurchaseListResponse(BaseModel):
    """Respuesta de listado con paginación"""
    items: List[PurchaseBase]
    total: int
    page: int
    page_size: int
    total_pages: int


class PurchaseStats(BaseModel):
    """Estadísticas de compras"""
    total_compras: int
    monto_total: float
    compras_mes_actual: int
    monto_mes_actual: float
    proveedor_mas_frecuente: Optional[str] = None
