# Modelos SQLAlchemy para Clientes y Vehículos
# Compatibles con el esquema de lubricentroMal (SQLite)

from sqlalchemy import Column, Integer, String, Text, Float, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import date
from app.db.base_class import Base


class Client(Base):
    """
    Tabla: clientes
    Modelo compatible con lubricentroMal
    Multi-tenant: aislado por lubricentro_id
    """
    __tablename__ = "clientes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    lubricentro_id = Column(Integer, ForeignKey("lubricentros.id", ondelete="CASCADE"), nullable=True, index=True)
    nombre = Column(String, nullable=False, index=True)
    email = Column(String, nullable=True, index=True)
    telefono = Column(String, nullable=True)
    direccion = Column(String, nullable=True)
    notas = Column(Text, nullable=True)
    fecha_registro = Column(String, nullable=True, default=lambda: date.today().isoformat())

    # Relaciones
    lubricentro = relationship("Lubricentro", back_populates="clientes")
    vehiculos = relationship("Vehicle", back_populates="cliente", cascade="all, delete-orphan")
    historial_facturas = relationship("HistorialFactura", back_populates="cliente", cascade="all, delete-orphan")
    visitas = relationship("Visit", back_populates="cliente", cascade="all, delete-orphan")
    turnos = relationship("Appointment", back_populates="cliente_rel", foreign_keys="Appointment.cliente_id")


class Vehicle(Base):
    """
    Tabla: vehiculos
    Modelo compatible con lubricentroMal
    """
    __tablename__ = "vehiculos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id", ondelete="CASCADE"), nullable=False)
    descripcion = Column(String, nullable=False)
    marca = Column(String, nullable=True)
    version = Column(String, nullable=True)
    modelo = Column(String, nullable=True)
    patente = Column(String, nullable=True, index=True)
    kilometraje = Column(Float, default=0)
    activo = Column(Boolean, default=True)  # Campo para activar/desactivar vehículo

    # Relación
    cliente = relationship("Client", back_populates="vehiculos")


class HistorialFactura(Base):
    """
    Tabla: historial_facturas
    Modelo compatible con lubricentroMal
    NOTA: Esta tabla no existía en lubricentroM, se agrega para compatibilidad
    """
    __tablename__ = "historial_facturas"

    id = Column(Integer, primary_key=True, autoincrement=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id", ondelete="CASCADE"), nullable=False)
    fecha = Column(String, nullable=False)  # Formato TEXT como en SQLite original

    # Relación
    cliente = relationship("Client", back_populates="historial_facturas")


class Visit(Base):
    """
    Tabla: visitas
    Registra cada visita del cliente al lubricentro (desde facturación)
    """
    __tablename__ = "visitas"

    id = Column(Integer, primary_key=True, autoincrement=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id", ondelete="CASCADE"), nullable=False, index=True)
    comprobante_id = Column(Integer, ForeignKey("comprobantes.id", ondelete="SET NULL"), nullable=True)
    fecha = Column(String, nullable=False)  # Fecha de la visita
    kilometraje = Column(Float, default=0)  # KM del vehículo al momento de la visita
    vehiculo_descripcion = Column(String, nullable=True)  # Descripción del vehículo
    observacion = Column(Text, nullable=True)  # Notas/observación del día
    lubricentro_id = Column(Integer, ForeignKey("lubricentros.id", ondelete="CASCADE"), nullable=True, index=True)

    # Relaciones
    cliente = relationship("Client", back_populates="visitas")
    lubricentro = relationship("Lubricentro")
