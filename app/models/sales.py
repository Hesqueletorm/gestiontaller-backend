# Modelos SQLAlchemy para Facturación (Comprobantes)
# Compatibles con el esquema de lubricentroMal (SQLite)

from sqlalchemy import Column, Integer, String, Float, Text, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.db.base_class import Base


class Sale(Base):
    """
    Tabla: comprobantes
    Modelo compatible con lubricentroMal
    Multi-tenant: aislado por lubricentro_id
    """
    __tablename__ = "comprobantes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    lubricentro_id = Column(Integer, ForeignKey("lubricentros.id", ondelete="CASCADE"), nullable=True, index=True)
    fecha = Column(String, nullable=False)  # Formato TEXT como en SQLite original
    tipo = Column(String, nullable=False)  # Factura A/B/C, Nota Crédito, Presupuesto
    punto_venta = Column(String, nullable=False)
    numero = Column(String, nullable=False)
    metodo_pago = Column(String, default="Efectivo")
    
    # Datos del cliente (snapshot)
    cliente_nombre = Column(String, nullable=False)
    cliente_dni = Column(String, default="")
    cliente_cuit = Column(String, default="")
    cliente_email = Column(String, default="")
    cliente_telefono = Column(String, default="")
    domicilio = Column(String, default="")
    condicion_iva = Column(String, default="")
    
    # Totales
    subtotal = Column(Float, nullable=False)
    iva = Column(Float, nullable=False)
    total = Column(Float, nullable=False)
    observaciones = Column(Text, default="")

    # Relaciones
    lubricentro = relationship("Lubricentro", back_populates="ventas")
    items = relationship("SaleItem", back_populates="comprobante", cascade="all, delete-orphan")
    vehiculos = relationship("SaleVehicle", back_populates="comprobante", cascade="all, delete-orphan")

    # Índice único para lubricentro_id + punto_venta + numero
    __table_args__ = (
        Index('idx_comp_lubri_pv_num', 'lubricentro_id', 'punto_venta', 'numero', unique=True),
    )


class SaleItem(Base):
    """
    Tabla: comprobante_items
    Modelo compatible con lubricentroMal
    """
    __tablename__ = "comprobante_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    comprobante_id = Column(Integer, ForeignKey("comprobantes.id", ondelete="CASCADE"), nullable=False)
    articulo = Column(String, nullable=False)
    cantidad = Column(Float, nullable=False)
    precio_unitario = Column(Float, nullable=False)
    iva_porcentaje = Column(Float, nullable=False)
    subtotal = Column(Float, nullable=False)
    total = Column(Float, nullable=False)
    
    # Nuevos campos para diferenciar productos y servicios
    es_servicio = Column(Integer, default=0)  # 0 = producto, 1 = servicio
    categoria = Column(String, default="")  # Categoría del servicio

    # Relación
    comprobante = relationship("Sale", back_populates="items")


class SaleVehicle(Base):
    """
    Tabla: comprobante_vehiculos
    Modelo compatible con lubricentroMal
    """
    __tablename__ = "comprobante_vehiculos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    comprobante_id = Column(Integer, ForeignKey("comprobantes.id", ondelete="CASCADE"), nullable=False)
    descripcion = Column(String, nullable=False)
    kilometraje = Column(Float, default=0)

    # Relación
    comprobante = relationship("Sale", back_populates="vehiculos")
