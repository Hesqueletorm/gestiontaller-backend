from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime


# --- Sale Items ---
class SaleItemBase(BaseModel):
    articulo: str
    cantidad: float
    precio_unitario: float
    iva_porcentaje: float = 21.0


class SaleItemCreate(SaleItemBase):
    stock_id: Optional[int] = None  # ID del producto en stock (opcional)
    es_servicio: int = 0  # 0 = producto, 1 = servicio
    categoria: Optional[str] = None  # Categoría del servicio


class SaleItem(SaleItemBase):
    id: int
    subtotal: float
    total: float
    comprobante_id: int
    es_servicio: int = 0
    categoria: Optional[str] = None

    class Config:
        from_attributes = True


# --- Sale Vehicles ---
class SaleVehicleBase(BaseModel):
    descripcion: str
    kilometraje: float = 0.0


class SaleVehicleCreate(SaleVehicleBase):
    pass


class SaleVehicle(SaleVehicleBase):
    id: int
    comprobante_id: int

    class Config:
        from_attributes = True


# --- Sales / Comprobantes ---
class SaleCreate(BaseModel):
    """Schema para crear un nuevo comprobante"""
    tipo: str = "Factura B"
    punto_venta: str = "0001"
    numero: Optional[str] = None  # Si es None, se auto-genera
    metodo_pago: str = "Efectivo"
    fecha: Optional[str] = None  # Si es None, se usa fecha actual

    # Datos del cliente
    cliente_id: Optional[int] = None  # ID del cliente registrado (para crear visita)
    cliente_nombre: str
    cliente_dni: Optional[str] = None
    cliente_cuit: Optional[str] = None
    cliente_email: Optional[str] = None
    cliente_telefono: Optional[str] = None
    domicilio: Optional[str] = None
    condicion_iva: Optional[str] = None

    observaciones: Optional[str] = None

    # Items y vehículos
    items: List[SaleItemCreate] = []
    vehiculos: List[SaleVehicleCreate] = []  # Múltiples vehículos


class SaleBase(BaseModel):
    """Schema base para lectura de comprobantes"""
    id: int
    fecha: str
    tipo: str
    punto_venta: str
    numero: str
    metodo_pago: str
    cliente_nombre: str
    subtotal: float
    iva: float
    total: float

    class Config:
        from_attributes = True


class Sale(SaleBase):
    """Schema de comprobante con items y vehículos"""
    cliente_dni: Optional[str] = None
    cliente_cuit: Optional[str] = None
    cliente_email: Optional[str] = None
    cliente_telefono: Optional[str] = None
    domicilio: Optional[str] = None
    condicion_iva: Optional[str] = None
    observaciones: Optional[str] = None

    items: List[SaleItem] = []
    vehiculos: List[SaleVehicle] = []

    class Config:
        from_attributes = True


class SaleListItem(BaseModel):
    """Schema para listado de comprobantes (resumen)"""
    id: int
    fecha: str
    tipo: str
    numero: str
    cliente_nombre: str
    total: float
    vehiculos_desc: Optional[str] = None  # Descripción concatenada de vehículos

    class Config:
        from_attributes = True


class SaleFilter(BaseModel):
    """Filtros para búsqueda de comprobantes"""
    cliente: Optional[str] = None
    vehiculo: Optional[str] = None
    desde: Optional[str] = None  # Fecha desde (YYYY-MM-DD)
    hasta: Optional[str] = None  # Fecha hasta (YYYY-MM-DD)


class NextNumberResponse(BaseModel):
    """Respuesta para obtener siguiente número de comprobante"""
    punto_venta: str
    numero: str
