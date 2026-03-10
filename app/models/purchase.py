# Modelos SQLAlchemy para Compras (Ingreso de Stock)
# Multi-tenant: aislado por lubricentro_id

from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base_class import Base


class Purchase(Base):
    """
    Tabla: compras
    Registro de compras a proveedores para ingreso de stock
    Multi-tenant: aislado por lubricentro_id
    """
    __tablename__ = "compras"

    id = Column(Integer, primary_key=True, autoincrement=True)
    lubricentro_id = Column(Integer, ForeignKey("lubricentros.id", ondelete="CASCADE"), nullable=True, index=True)
    
    # Datos de la compra
    fecha = Column(DateTime, server_default=func.now(), nullable=False)
    numero_factura = Column(String, nullable=True)  # Factura del proveedor
    
    # Datos del proveedor
    proveedor_nombre = Column(String, nullable=False)
    proveedor_cuit = Column(String, nullable=True)
    proveedor_telefono = Column(String, nullable=True)
    proveedor_email = Column(String, nullable=True)
    
    # Método de pago
    metodo_pago = Column(String, default="Efectivo")  # Efectivo, Transferencia, Cheque, Cuenta Corriente
    
    # Totales
    subtotal = Column(Float, nullable=False, default=0)
    iva = Column(Float, nullable=False, default=0)
    total = Column(Float, nullable=False, default=0)
    
    # Observaciones
    observaciones = Column(Text, nullable=True)
    
    # Metadatos
    created_at = Column(DateTime, server_default=func.now())
    created_by = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    
    # Relaciones
    lubricentro = relationship("Lubricentro", back_populates="compras")
    items = relationship("PurchaseItem", back_populates="compra", cascade="all, delete-orphan")
    
    # Índices
    __table_args__ = (
        Index('idx_compras_fecha', 'lubricentro_id', 'fecha'),
        Index('idx_compras_proveedor', 'lubricentro_id', 'proveedor_nombre'),
    )


class PurchaseItem(Base):
    """
    Tabla: compra_items
    Items individuales de cada compra
    """
    __tablename__ = "compra_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    compra_id = Column(Integer, ForeignKey("compras.id", ondelete="CASCADE"), nullable=False)
    
    # Producto (puede ser existente o nuevo)
    producto_id = Column(Integer, ForeignKey("stock_productos.id", ondelete="SET NULL"), nullable=True)
    articulo = Column(String, nullable=False)  # Nombre del artículo
    codigo = Column(String, nullable=True)  # Código del producto
    
    # Cantidades y precios
    cantidad = Column(Float, nullable=False)
    precio_unitario = Column(Float, nullable=False)
    iva_porcentaje = Column(Float, nullable=False, default=21.0)
    subtotal = Column(Float, nullable=False)
    total = Column(Float, nullable=False)
    
    # Relaciones
    compra = relationship("Purchase", back_populates="items")
    # Sin backref a Producto para evitar conflictos de SQLAlchemy
