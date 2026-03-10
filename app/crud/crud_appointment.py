from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.crud.base import CRUDBase
from app.models.appointments import Appointment
from app.schemas.appointment_schema import AppointmentCreate, AppointmentUpdate


class CRUDAppointment(CRUDBase[Appointment, AppointmentCreate, AppointmentUpdate]):
    
    def get_by_lubricentro(
        self, db: Session, *, lubricentro_id: int, skip: int = 0, limit: int = 100
    ) -> List[Appointment]:
        """Obtener todos los turnos de un lubricentro"""
        return (
            db.query(Appointment)
            .filter(Appointment.lubricentro_id == lubricentro_id)
            .order_by(Appointment.fecha, Appointment.hora)
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def get_by_fecha(
        self, db: Session, *, lubricentro_id: int, fecha: str
    ) -> List[Appointment]:
        """Obtener turnos de un día específico"""
        return (
            db.query(Appointment)
            .filter(
                and_(
                    Appointment.lubricentro_id == lubricentro_id,
                    Appointment.fecha == fecha
                )
            )
            .order_by(Appointment.hora)
            .all()
        )
    
    def get_by_rango(
        self, db: Session, *, lubricentro_id: int, fecha_desde: str, fecha_hasta: str
    ) -> List[Appointment]:
        """Obtener turnos en un rango de fechas"""
        return (
            db.query(Appointment)
            .filter(
                and_(
                    Appointment.lubricentro_id == lubricentro_id,
                    Appointment.fecha >= fecha_desde,
                    Appointment.fecha <= fecha_hasta
                )
            )
            .order_by(Appointment.fecha, Appointment.hora)
            .all()
        )
    
    def check_slot_disponible(
        self, db: Session, *, lubricentro_id: int, fecha: str, hora: str, exclude_id: Optional[int] = None
    ) -> bool:
        """Verificar si un slot está disponible"""
        query = db.query(Appointment).filter(
            and_(
                Appointment.lubricentro_id == lubricentro_id,
                Appointment.fecha == fecha,
                Appointment.hora == hora
            )
        )
        if exclude_id:
            query = query.filter(Appointment.id != exclude_id)
        return query.first() is None
    
    def create_with_lubricentro(
        self, db: Session, *, obj_in: AppointmentCreate, lubricentro_id: int
    ) -> Appointment:
        """Crear turno asociado a un lubricentro"""
        db_obj = Appointment(
            lubricentro_id=lubricentro_id,
            fecha=obj_in.fecha,
            hora=obj_in.hora,
            cliente=obj_in.cliente,
            cliente_id=getattr(obj_in, 'cliente_id', None),  # FK opcional
            vehiculo=obj_in.vehiculo or "",
            servicio=obj_in.servicio or "",
            notas=obj_in.notas or "",
            duracion=obj_in.duracion or 30
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def update_turno(
        self, db: Session, *, db_obj: Appointment, obj_in: AppointmentUpdate
    ) -> Appointment:
        """Actualizar turno"""
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj


appointment = CRUDAppointment(Appointment)
