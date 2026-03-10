# Modelo SQLAlchemy para Lotes de Productos
# Multi-tenant: aislado por lubricentro_id

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base_class import Base


class ProductLote(Base):
    """
    Tabla: stock_lotes
    Lotes de productos con cantidades y fechas de vencimiento individuales.
    Permite tener el mismo producto con diferentes fechas de vencimiento.
    Multi-tenant: aislado por lubricentro_id
    """
    __tablename__ = "stock_lotes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    lubricentro_id = Column(Integer, ForeignKey("lubricentros.id", ondelete="CASCADE"), nullable=False, index=True)
    producto_id = Column(Integer, ForeignKey("stock_productos.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Cantidad en este lote específico
    cantidad = Column(Float, nullable=False, default=0)
    
    # Fecha de vencimiento del lote (formato YYYY-MM-DD)
    fecha_vencimiento = Column(String, nullable=True)
    
    # Metadatos
    fecha_ingreso = Column(DateTime, server_default=func.now(), nullable=False)
    compra_id = Column(Integer, ForeignKey("compras.id", ondelete="SET NULL"), nullable=True)
    
    # Relaciones
    producto = relationship("Producto", backref="lotes")
    
    # Índices para consultas frecuentes
    __table_args__ = (
        Index('idx_lotes_producto', 'lubricentro_id', 'producto_id'),
        Index('idx_lotes_vencimiento', 'lubricentro_id', 'fecha_vencimiento'),
    )
