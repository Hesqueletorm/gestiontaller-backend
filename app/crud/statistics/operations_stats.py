"""
Estadísticas de Operaciones/Turnos
"""
from typing import List
from datetime import date, timedelta
from calendar import monthrange
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.models.appointments import Appointment
from . import get_color


def get_operations_stats(
    db: Session,
    lubricentro_id: int,
    date_from: date = None,
    date_to: date = None,
) -> dict:
    """Obtener estadísticas de turnos y operaciones"""
    hoy = date.today()
    mes_inicio = hoy.replace(day=1).isoformat()
    hoy_str = hoy.isoformat()
    
    # Turnos del mes
    turnos_mes = db.query(func.count(Appointment.id)).filter(
        Appointment.lubricentro_id == lubricentro_id,
        Appointment.fecha >= mes_inicio
    ).scalar() or 0
    
    # Turnos de hoy
    turnos_hoy = db.query(func.count(Appointment.id)).filter(
        Appointment.lubricentro_id == lubricentro_id,
        Appointment.fecha == hoy_str
    ).scalar() or 0
    
    # Por día de semana
    DIAS = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']
    por_dia = {d: 0 for d in DIAS}
    
    turnos_recientes = db.query(Appointment.fecha).filter(
        Appointment.lubricentro_id == lubricentro_id,
        Appointment.fecha >= (hoy - timedelta(days=90)).isoformat()
    ).all()
    
    for t in turnos_recientes:
        try:
            fecha = date.fromisoformat(t.fecha)
            dia_idx = fecha.weekday()
            por_dia[DIAS[dia_idx]] += 1
        except:
            pass
    
    # Por hora
    HORAS = [f"{h:02d}:00" for h in range(8, 20)]
    por_hora = {h: 0 for h in HORAS}
    
    turnos_hora = db.query(Appointment.hora).filter(
        Appointment.lubricentro_id == lubricentro_id,
        Appointment.fecha >= (hoy - timedelta(days=90)).isoformat()
    ).all()
    
    for t in turnos_hora:
        hora = t.hora[:2] + ":00" if t.hora else None
        if hora in por_hora:
            por_hora[hora] += 1
    
    # Por servicio
    por_servicio = db.query(
        Appointment.servicio,
        func.count(Appointment.id).label('cantidad')
    ).filter(
        Appointment.lubricentro_id == lubricentro_id,
        Appointment.servicio.isnot(None),
        Appointment.servicio != ""
    ).group_by(Appointment.servicio).order_by(desc('cantidad')).limit(5).all()
    
    # Evolución de turnos
    evolucion = get_monthly_appointments_evolution(db, lubricentro_id)
    
    return {
        "turnos_mes": turnos_mes,
        "turnos_hoy": turnos_hoy,
        "servicios_realizados": turnos_mes,
        "por_dia_semana": [
            {"label": d, "value": float(v), "color": get_color(i)}
            for i, (d, v) in enumerate(por_dia.items())
        ],
        "por_hora": [
            {"label": h, "value": float(v), "color": get_color(i)}
            for i, (h, v) in enumerate(por_hora.items())
        ],
        "por_servicio": [
            {"label": r.servicio, "value": float(r.cantidad), "color": get_color(i)}
            for i, r in enumerate(por_servicio)
        ],
        "evolucion_turnos": evolucion,
    }


def get_monthly_appointments_evolution(db: Session, lubricentro_id: int, months: int = 12) -> List[dict]:
    """Evolución de turnos por mes"""
    result = []
    hoy = date.today()
    
    for i in range(months - 1, -1, -1):
        target_month = hoy.month - i
        target_year = hoy.year
        while target_month <= 0:
            target_month += 12
            target_year -= 1
        
        _, last_day = monthrange(target_year, target_month)
        start = date(target_year, target_month, 1)
        end = date(target_year, target_month, last_day)
        
        count = db.query(func.count(Appointment.id)).filter(
            Appointment.lubricentro_id == lubricentro_id,
            Appointment.fecha >= start.isoformat(),
            Appointment.fecha <= end.isoformat()
        ).scalar() or 0
        
        result.append({
            "date": start.strftime("%Y-%m"),
            "value": float(count),
            "label": start.strftime("%b %Y")
        })
    
    return result
