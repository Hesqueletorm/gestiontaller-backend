from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime


# --- Categorías ---
class CategoryBase(BaseModel):
    nombre: str


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    nombre: Optional[str] = None


class Category(CategoryBase):
    id: int

    class Config:
        from_attributes = True


# --- Productos ---
class ProductBase(BaseModel):
    codigo: Optional[str] = None
    nombre: str
    descripcion: Optional[str] = None
    cantidad: float = 0.0
    fecha_vencimiento: Optional[str] = None  # Formato YYYY-MM-DD
    tiene_vencimiento: bool = False  # True si el producto maneja fecha de vencimiento
    alerta: int = 0  # 1 = tiene alerta activa
    ubicacion_a: Optional[str] = None
    ubicacion_b: Optional[str] = None
    ubicacion_c: Optional[str] = None
    categoria: Optional[str] = None  # Nombre de la categoría


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    codigo: Optional[str] = None
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    cantidad: Optional[float] = None
    fecha_vencimiento: Optional[str] = None
    tiene_vencimiento: Optional[bool] = None
    alerta: Optional[int] = None
    ubicacion_a: Optional[str] = None
    ubicacion_b: Optional[str] = None
    ubicacion_c: Optional[str] = None
    categoria: Optional[str] = None


class Product(ProductBase):
    id: int
    fecha_creacion: Optional[datetime] = None

    class Config:
        from_attributes = True


class ProductFilter(BaseModel):
    """Filtros de búsqueda de productos"""
    nombre: Optional[str] = None
    codigo: Optional[str] = None
    categoria: Optional[str] = None
    solo_alerta: bool = False


class ProductListResponse(BaseModel):
    """Respuesta de listado con paginación"""
    items: List[Product]
    total: int
    page: int
    page_size: int
    total_pages: int
