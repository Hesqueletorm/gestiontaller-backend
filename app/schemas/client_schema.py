from typing import List, Optional, Any
from pydantic import BaseModel

# --- Vehicles ---
class VehicleBase(BaseModel):
    descripcion: str
    activo: bool = True

class VehicleCreate(VehicleBase):
    activo: bool = True

class VehicleUpdate(BaseModel):
    descripcion: Optional[str] = None
    activo: Optional[bool] = None

class Vehicle(VehicleBase):
    id: int
    cliente_id: int
    marca: Optional[str] = None
    version: Optional[str] = None
    modelo: Optional[str] = None
    patente: Optional[str] = None
    kilometraje: Optional[float] = 0
    activo: bool = True

    class Config:
        from_attributes = True

class VehicleToggleActive(BaseModel):
    """Schema para toggle de activo"""
    activo: bool


class VehicleWithKm(BaseModel):
    """Vehículo con último kilometraje conocido"""
    id: int
    descripcion: str
    marca: Optional[str] = None
    version: Optional[str] = None
    modelo: Optional[str] = None
    patente: Optional[str] = None
    ultimo_km: Optional[float] = None
    ultima_fecha: Optional[str] = None
    activo: bool = True

    class Config:
        from_attributes = True


# --- Visits (Historial de visitas) ---
class VisitItemResumen(BaseModel):
    """Resumen de un item (producto o servicio) de una visita"""
    articulo: str
    cantidad: float
    precio_unitario: float
    es_servicio: bool = False
    categoria: Optional[str] = None

    class Config:
        from_attributes = True


class VisitBase(BaseModel):
    fecha: str
    kilometraje: Optional[float] = 0
    vehiculo_descripcion: Optional[str] = None
    observacion: Optional[str] = None

class VisitCreate(VisitBase):
    cliente_id: int
    comprobante_id: Optional[int] = None
    lubricentro_id: Optional[int] = None

class Visit(VisitBase):
    id: int
    cliente_id: int
    comprobante_id: Optional[int] = None
    productos: List[VisitItemResumen] = []
    servicios: List[VisitItemResumen] = []

    class Config:
        from_attributes = True


# --- Clients ---
class ClientBase(BaseModel):
    nombre: str
    email: Optional[str] = None
    telefono: Optional[str] = None
    direccion: Optional[str] = None
    notas: Optional[str] = None

class ClientCreate(ClientBase):
    pass

class ClientUpdate(ClientBase):
    pass

# Schema para sincronizar cliente con vehículos desde facturación
class VehicleSyncData(BaseModel):
    """Datos de vehículo para sincronización"""
    descripcion: Optional[str] = None
    marca: Optional[str] = None
    version: Optional[str] = None
    modelo: Optional[str] = None
    patente: Optional[str] = None
    kilometraje: Optional[float] = 0

class ClientSyncRequest(ClientBase):
    """Request para sincronizar cliente con vehículos"""
    vehiculos: Optional[List[VehicleSyncData]] = []

class Client(ClientBase):
    id: int
    vehiculos: List[Vehicle] = []

    class Config:
        from_attributes = True


class ClientWithVisits(BaseModel):
    """Cliente con historial de visitas incluido"""
    id: int
    nombre: str
    email: Optional[str] = None
    telefono: Optional[str] = None
    direccion: Optional[str] = None
    notas: Optional[str] = None
    vehiculos: List[VehicleWithKm] = []
    visitas: List[Visit] = []
    total_visitas: int = 0

    class Config:
        from_attributes = True
        from_attributes = True
