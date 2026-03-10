# Modelo SQLAlchemy para Turnos
# Compatible con el esquema de lubricentroMal (SQLite)

from sqlalchemy import Column, Integer, String, Text, Index, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base_class import Base


class Appointment(Base):
    """
    Tabla: turnos
    Modelo compatible con lubricentroMal
    Multi-tenant: aislado por lubricentro_id
    """
    __tablename__ = "turnos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    lubricentro_id = Column(Integer, ForeignKey("lubricentros.id", ondelete="CASCADE"), nullable=True, index=True)
    fecha = Column(String, nullable=False, index=True)  # Formato YYYY-MM-DD
    hora = Column(String, nullable=False)  # Formato HH:MM
    cliente = Column(String, nullable=False)  # Nombre del cliente
    cliente_id = Column(Integer, ForeignKey("clientes.id", ondelete="SET NULL"), nullable=True, index=True)  # FK opcional a clientes
    vehiculo = Column(String, default="")
    servicio = Column(String, default="")
    notas = Column(Text, default="")
    duracion = Column(Integer, default=30)  # Duración en minutos

    # Relaciones
    lubricentro = relationship("Lubricentro", back_populates="turnos")
    cliente_rel = relationship("Client", back_populates="turnos", foreign_keys=[cliente_id])

    # Índice único para evitar duplicados por franja horaria POR LUBRICENTRO
    __table_args__ = (
        Index('idx_turnos_lubri_fecha_hora', 'lubricentro_id', 'fecha', 'hora', unique=True),
    )

