# Modelo SQLAlchemy para Proveedores
# Multi-tenant: aislado por lubricentro_id

from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime, ForeignKey, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base_class import Base


class Supplier(Base):
    """
    Tabla: proveedores
    Registro de proveedores del lubricentro
    Multi-tenant: aislado por lubricentro_id
    """
    __tablename__ = "proveedores"

    id = Column(Integer, primary_key=True, autoincrement=True)
    lubricentro_id = Column(Integer, ForeignKey("lubricentros.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Datos del proveedor
    nombre = Column(String(200), nullable=False)
    cuit = Column(String(20), nullable=True)
    telefono = Column(String(50), nullable=True)
    email = Column(String(100), nullable=True)
    direccion = Column(String(300), nullable=True)
    
    # Información adicional
    contacto = Column(String(100), nullable=True)  # Nombre de contacto
    rubro = Column(String(100), nullable=True)  # Ej: Aceites, Filtros, Repuestos
    notas = Column(Text, nullable=True)
    
    # Estado
    activo = Column(Boolean, default=True, nullable=False)
    
    # Metadatos
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relación con lubricentro
    lubricentro = relationship("Lubricentro", back_populates="proveedores")
    
    # Índices
    __table_args__ = (
        Index('idx_proveedores_nombre', 'lubricentro_id', 'nombre'),
        Index('idx_proveedores_cuit', 'lubricentro_id', 'cuit'),
        Index('idx_proveedores_activo', 'lubricentro_id', 'activo'),
    )
