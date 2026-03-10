# Modelos SQLAlchemy para Stock (Productos y Categorías)
# Compatibles con el esquema de lubricentroMal (SQLite)

from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base_class import Base


class Category(Base):
    """
    Tabla: stock_categorias
    Modelo compatible con lubricentroMal
    Multi-tenant: aislado por lubricentro_id
    """
    __tablename__ = "stock_categorias"

    id = Column(Integer, primary_key=True, autoincrement=True)
    lubricentro_id = Column(Integer, ForeignKey("lubricentros.id", ondelete="CASCADE"), nullable=True, index=True)
    nombre = Column(String, nullable=False)


class Producto(Base):
    """
    Tabla: stock_productos
    Modelo compatible con lubricentroMal
    Multi-tenant: aislado por lubricentro_id
    """
    __tablename__ = "stock_productos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    lubricentro_id = Column(Integer, ForeignKey("lubricentros.id", ondelete="CASCADE"), nullable=True, index=True)
    codigo = Column(String, nullable=True, index=True)
    nombre = Column(String, nullable=False, index=True)
    cantidad = Column(Float, nullable=False, default=0)
    fecha_vencimiento = Column(String, nullable=True)  # Formato TEXT como en SQLite original
    tiene_vencimiento = Column(Boolean, nullable=False, default=False)  # True si el producto maneja fecha de vencimiento
    alerta = Column(Integer, nullable=False, default=0)  # Umbral de alerta de stock
    ubicacion_a = Column(String, nullable=True)
    ubicacion_b = Column(String, nullable=True)
    ubicacion_c = Column(String, nullable=True)
    categoria = Column(String, nullable=True)  # Nombre de la categoría
    descripcion = Column(Text, nullable=True)
    fecha_creacion = Column(DateTime, server_default=func.now())
    
    # Relaciones
    lubricentro = relationship("Lubricentro", back_populates="productos")


# Alias para compatibilidad con imports que usen nombres en inglés
Product = Producto


class Servicio(Base):
    """
    Tabla: servicios
    Modelo para servicios del lubricentro (mano de obra, etc.)
    Multi-tenant: aislado por lubricentro_id
    """
    __tablename__ = "servicios"

    id = Column(Integer, primary_key=True, autoincrement=True)
    lubricentro_id = Column(Integer, ForeignKey("lubricentros.id", ondelete="CASCADE"), nullable=True, index=True)
    codigo = Column(String, nullable=True, index=True)
    nombre = Column(String, nullable=False, index=True)
    descripcion = Column(Text, nullable=True)
    precio = Column(Float, nullable=False, default=0)
    categoria = Column(String, nullable=True)
    activo = Column(Integer, nullable=False, default=1)  # 1=activo, 0=inactivo
    fecha_creacion = Column(DateTime, server_default=func.now())
    
    # Relaciones
    lubricentro = relationship("Lubricentro", back_populates="servicios")


# Alias
Service = Servicio


class StockAdjustment(Base):
    """
    Tabla: stock_ajustes
    Registro de ajustes de stock (egresos controlados)
    Tipos: vencimiento, descarte, consumo_interno
    Multi-tenant: aislado por lubricentro_id
    """
    __tablename__ = "stock_ajustes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    lubricentro_id = Column(Integer, ForeignKey("lubricentros.id", ondelete="CASCADE"), nullable=False, index=True)
    producto_id = Column(Integer, ForeignKey("stock_productos.id", ondelete="CASCADE"), nullable=False, index=True)
    tipo_ajuste = Column(String, nullable=False)  # vencimiento | descarte | consumo_interno
    cantidad = Column(Float, nullable=False)  # Cantidad a restar (siempre positiva)
    motivo = Column(Text, nullable=True)  # Descripción del ajuste
    fecha = Column(DateTime, server_default=func.now(), nullable=False)
    created_by = Column(Integer, ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True)
    # Sin relaciones explícitas para evitar conflictos - se hace join manual en CRUD
