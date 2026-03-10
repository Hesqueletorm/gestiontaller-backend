"""
Estadísticas de Ventas
"""
from typing import List
from datetime import date
from calendar import monthrange
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.models.sales import Sale, SaleItem
from . import get_color


def get_sales_stats(
    db: Session,
    lubricentro_id: int,
    date_from: date = None,
    date_to: date = None,
) -> dict:
    """Obtener estadísticas de ventas"""
    if not date_from:
        date_from = date.today().replace(month=1, day=1)
    if not date_to:
        date_to = date.today()
    
    date_from_str = date_from.isoformat()
    date_to_str = date_to.isoformat()
    
    # KPIs principales
    totales = db.query(
        func.count(Sale.id).label('cantidad'),
        func.coalesce(func.sum(Sale.total), 0).label('total'),
        func.coalesce(func.sum(Sale.iva), 0).label('iva'),
        func.coalesce(func.avg(Sale.total), 0).label('promedio')
    ).filter(
        Sale.lubricentro_id == lubricentro_id,
        Sale.fecha >= date_from_str,
        Sale.fecha <= date_to_str
    ).first()
    
    # Por tipo de comprobante
    por_tipo = db.query(
        Sale.tipo,
        func.count(Sale.id).label('cantidad'),
        func.sum(Sale.total).label('total')
    ).filter(
        Sale.lubricentro_id == lubricentro_id,
        Sale.fecha >= date_from_str,
        Sale.fecha <= date_to_str
    ).group_by(Sale.tipo).all()
    
    # Por método de pago
    por_metodo = db.query(
        Sale.metodo_pago,
        func.count(Sale.id).label('cantidad'),
        func.sum(Sale.total).label('total')
    ).filter(
        Sale.lubricentro_id == lubricentro_id,
        Sale.fecha >= date_from_str,
        Sale.fecha <= date_to_str
    ).group_by(Sale.metodo_pago).all()
    
    # Top productos (excluyendo servicios)
    top_productos = db.query(
        SaleItem.articulo,
        func.sum(SaleItem.cantidad).label('cantidad'),
        func.sum(SaleItem.total).label('total')
    ).join(Sale).filter(
        Sale.lubricentro_id == lubricentro_id,
        Sale.fecha >= date_from_str,
        Sale.fecha <= date_to_str,
        SaleItem.es_servicio == 0
    ).group_by(SaleItem.articulo).order_by(desc('total')).limit(10).all()
    
    # Top servicios
    top_servicios = db.query(
        SaleItem.articulo,
        func.sum(SaleItem.cantidad).label('cantidad'),
        func.sum(SaleItem.total).label('total')
    ).join(Sale).filter(
        Sale.lubricentro_id == lubricentro_id,
        Sale.fecha >= date_from_str,
        Sale.fecha <= date_to_str,
        SaleItem.es_servicio == 1
    ).group_by(SaleItem.articulo).order_by(desc('total')).limit(10).all()
    
    # Top clientes
    top_clientes = db.query(
        Sale.cliente_nombre,
        func.count(Sale.id).label('cantidad'),
        func.sum(Sale.total).label('total')
    ).filter(
        Sale.lubricentro_id == lubricentro_id,
        Sale.fecha >= date_from_str,
        Sale.fecha <= date_to_str
    ).group_by(Sale.cliente_nombre).order_by(desc('total')).limit(10).all()
    
    # Evolución mensual
    evolucion = get_monthly_sales_evolution(db, lubricentro_id)
    
    return {
        "total_facturacion": float(totales.total or 0),
        "total_comprobantes": int(totales.cantidad or 0),
        "ticket_promedio": round(float(totales.promedio or 0), 2),
        "total_iva": float(totales.iva or 0),
        "evolucion_mensual": evolucion,
        "por_tipo_comprobante": [
            {"label": r.tipo, "value": float(r.total or 0), "color": get_color(i)}
            for i, r in enumerate(por_tipo)
        ],
        "por_metodo_pago": [
            {"label": r.metodo_pago, "value": float(r.total or 0), "color": get_color(i)}
            for i, r in enumerate(por_metodo)
        ],
        "top_productos": [
            {"name": r.articulo, "value": float(r.total or 0), "quantity": float(r.cantidad or 0)}
            for r in top_productos
        ],
        "top_servicios": [
            {"name": r.articulo, "value": float(r.total or 0), "quantity": float(r.cantidad or 0)}
            for r in top_servicios
        ],
        "top_clientes": [
            {"name": r.cliente_nombre, "value": float(r.total or 0), "quantity": int(r.cantidad or 0)}
            for r in top_clientes
        ],
    }


def get_monthly_sales_evolution(db: Session, lubricentro_id: int, months: int = 12) -> List[dict]:
    """Obtener evolución de ventas por mes"""
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
        
        total = db.query(func.coalesce(func.sum(Sale.total), 0)).filter(
            Sale.lubricentro_id == lubricentro_id,
            Sale.fecha >= start.isoformat(),
            Sale.fecha <= end.isoformat()
        ).scalar()
        
        result.append({
            "date": start.strftime("%Y-%m"),
            "value": float(total or 0),
            "label": start.strftime("%b %Y")
        })
    
    return result
