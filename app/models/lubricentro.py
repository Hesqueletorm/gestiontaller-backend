# Modelo SQLAlchemy para Lubricentros (Multi-tenant)

from sqlalchemy import Boolean, Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base_class import Base


class Lubricentro(Base):
    """
    Tabla: lubricentros
    Cada lubricentro es una entidad independiente con su propia configuración
    """
    __tablename__ = "lubricentros"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String, nullable=False, default="Mi Lubricentro")
    codigo = Column(String, unique=True, nullable=False, index=True)  # Código único para unirse
    
    # Configuración visual por defecto del lubricentro
    color_fondo = Column(String, default="#04060c")
    color_tematica = Column(String, default="#f2e71a")
    color_tematica2 = Column(String, default="#FFA000")
    color_letras = Column(String, default="#F5F7FA")
    tema = Column(String, default="dark")
    idioma = Column(String, default="Español")
    # Colores de la barra de identidad (gradiente 3 colores)
    color_identidad1 = Column(String, default="#FFA000")
    color_identidad2 = Column(String, default="#FBF7E3")
    color_identidad3 = Column(String, default="#0F172A")
    # Pesos (espacio/tamaño) de cada color en la barra de identidad
    peso_identidad1 = Column(Integer, default=33)
    peso_identidad2 = Column(Integer, default=34)
    peso_identidad3 = Column(Integer, default=33)
    
    # Configuración extra (JSON serializado)
    configuracion_extra = Column(Text, default="{}")
    
    # Metadatos
    fecha_creacion = Column(DateTime, server_default=func.now())
    activo = Column(Boolean, default=True)
    
    # Relaciones
    usuarios = relationship("User", back_populates="lubricentro")
    clientes = relationship("Client", back_populates="lubricentro")
    productos = relationship("Producto", back_populates="lubricentro")
    servicios = relationship("Servicio", back_populates="lubricentro")
    turnos = relationship("Appointment", back_populates="lubricentro")
    ventas = relationship("Sale", back_populates="lubricentro")
    compras = relationship("Purchase", back_populates="lubricentro")
    proveedores = relationship("Supplier", back_populates="lubricentro")
