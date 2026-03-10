"""
Estadísticas de Clientes
"""
from typing import List
from datetime import date
from calendar import monthrange
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.models.sales import Sale
from app.models.client import Client, Visit


def get_clients_stats(
    db: Session,
    lubricentro_id: int,
    date_from: date = None,
    date_to: date = None,
) -> dict:
    """Obtener estadísticas de clientes"""
    hoy = date.today()
    mes_actual_inicio = hoy.replace(day=1).isoformat()
    
    # Total clientes
    total_clientes = db.query(func.count(Client.id)).filter(
        Client.lubricentro_id == lubricentro_id
    ).scalar() or 0
    
    # Clientes nuevos este mes
    clientes_nuevos = db.query(func.count(Client.id)).filter(
        Client.lubricentro_id == lubricentro_id,
        Client.fecha_registro >= mes_actual_inicio
    ).scalar() or 0
    
    # Clientes con visitas
    clientes_con_visitas = db.query(func.count(func.distinct(Visit.cliente_id))).filter(
        Visit.lubricentro_id == lubricentro_id
    ).scalar() or 0
    
    # Top clientes por facturación
    top_facturacion = db.query(
        Sale.cliente_nombre,
        func.count(Sale.id).label('cantidad'),
        func.sum(Sale.total).label('total')
    ).filter(
        Sale.lubricentro_id == lubricentro_id
    ).group_by(Sale.cliente_nombre).order_by(desc('total')).limit(10).all()
    
    # Top clientes por visitas
    top_visitas = db.query(
        Client.nombre,
        func.count(Visit.id).label('cantidad')
    ).join(Visit, Client.id == Visit.cliente_id).filter(
        Client.lubricentro_id == lubricentro_id
    ).group_by(Client.id, Client.nombre).order_by(desc('cantidad')).limit(10).all()
    
    # Evoluciones
    evolucion_nuevos = get_monthly_new_clients_evolution(db, lubricentro_id)
    evolucion_visitas = get_monthly_visits_evolution(db, lubricentro_id)
    
    return {
        "total_clientes": total_clientes,
        "clientes_nuevos_mes": clientes_nuevos,
        "clientes_con_visitas": clientes_con_visitas,
        "frecuencia_promedio_dias": None,
        "evolucion_nuevos": evolucion_nuevos,
        "evolucion_visitas": evolucion_visitas,
        "top_clientes_facturacion": [
            {"name": r.cliente_nombre, "value": float(r.total or 0), "quantity": int(r.cantidad or 0)}
            for r in top_facturacion
        ],
        "top_clientes_visitas": [
            {"name": r.nombre, "value": 0, "quantity": int(r.cantidad or 0)}
            for r in top_visitas
        ],
    }


def get_monthly_new_clients_evolution(db: Session, lubricentro_id: int, months: int = 12) -> List[dict]:
    """Evolución de nuevos clientes por mes"""
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
        
        count = db.query(func.count(Client.id)).filter(
            Client.lubricentro_id == lubricentro_id,
            Client.fecha_registro >= start.isoformat(),
            Client.fecha_registro <= end.isoformat()
        ).scalar() or 0
        
        result.append({
            "date": start.strftime("%Y-%m"),
            "value": float(count),
            "label": start.strftime("%b %Y")
        })
    
    return result


def get_monthly_visits_evolution(db: Session, lubricentro_id: int, months: int = 12) -> List[dict]:
    """Evolución de visitas por mes"""
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
        
        count = db.query(func.count(Visit.id)).filter(
            Visit.lubricentro_id == lubricentro_id,
            Visit.fecha >= start.isoformat(),
            Visit.fecha <= end.isoformat()
        ).scalar() or 0
        
        result.append({
            "date": start.strftime("%Y-%m"),
            "value": float(count),
            "label": start.strftime("%b %Y")
        })
    
    return result
