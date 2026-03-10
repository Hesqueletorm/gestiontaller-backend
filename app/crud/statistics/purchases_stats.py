"""
Estadísticas de Compras
"""
from typing import List
from datetime import date, datetime
from calendar import monthrange
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.models.purchase import Purchase, PurchaseItem
from . import get_color


def get_purchases_stats(
    db: Session,
    lubricentro_id: int,
    date_from: date = None,
    date_to: date = None,
) -> dict:
    """Obtener estadísticas de compras"""
    if not date_from:
        date_from = date.today().replace(day=1)
    if not date_to:
        date_to = date.today()
    
    # KPIs
    totales = db.query(
        func.count(Purchase.id).label('cantidad'),
        func.coalesce(func.sum(Purchase.total), 0).label('total'),
        func.coalesce(func.sum(Purchase.iva), 0).label('iva'),
        func.coalesce(func.avg(Purchase.total), 0).label('promedio')
    ).filter(
        Purchase.lubricentro_id == lubricentro_id,
        Purchase.fecha >= date_from,
        Purchase.fecha <= date_to
    ).first()
    
    # Por proveedor
    por_proveedor = db.query(
        Purchase.proveedor_nombre,
        func.count(Purchase.id).label('cantidad'),
        func.sum(Purchase.total).label('total')
    ).filter(
        Purchase.lubricentro_id == lubricentro_id,
        Purchase.fecha >= date_from,
        Purchase.fecha <= date_to
    ).group_by(Purchase.proveedor_nombre).order_by(desc('total')).limit(5).all()
    
    # Por método de pago
    por_metodo = db.query(
        Purchase.metodo_pago,
        func.count(Purchase.id).label('cantidad'),
        func.sum(Purchase.total).label('total')
    ).filter(
        Purchase.lubricentro_id == lubricentro_id,
        Purchase.fecha >= date_from,
        Purchase.fecha <= date_to
    ).group_by(Purchase.metodo_pago).all()
    
    # Top productos comprados
    top_productos = db.query(
        PurchaseItem.articulo,
        func.sum(PurchaseItem.cantidad).label('cantidad'),
        func.sum(PurchaseItem.total).label('total')
    ).join(Purchase).filter(
        Purchase.lubricentro_id == lubricentro_id,
        Purchase.fecha >= date_from,
        Purchase.fecha <= date_to
    ).group_by(PurchaseItem.articulo).order_by(desc('total')).limit(10).all()
    
    # Evolución mensual
    evolucion = get_monthly_purchases_evolution(db, lubricentro_id)
    
    return {
        "total_compras": float(totales.total or 0),
        "cantidad_compras": int(totales.cantidad or 0),
        "compra_promedio": round(float(totales.promedio or 0), 2),
        "total_iva": float(totales.iva or 0),
        "evolucion_mensual": evolucion,
        "por_proveedor": [
            {"label": r.proveedor_nombre, "value": float(r.total or 0), "color": get_color(i)}
            for i, r in enumerate(por_proveedor)
        ],
        "por_metodo_pago": [
            {"label": r.metodo_pago, "value": float(r.total or 0), "color": get_color(i)}
            for i, r in enumerate(por_metodo)
        ],
        "top_proveedores": [
            {"name": r.proveedor_nombre, "value": float(r.total or 0), "quantity": int(r.cantidad or 0)}
            for r in por_proveedor
        ],
        "top_productos_comprados": [
            {"name": r.articulo, "value": float(r.total or 0), "quantity": float(r.cantidad or 0)}
            for r in top_productos
        ],
    }


def get_monthly_purchases_evolution(db: Session, lubricentro_id: int, months: int = 12) -> List[dict]:
    """Obtener evolución de compras por mes"""
    result = []
    hoy = date.today()
    
    for i in range(months - 1, -1, -1):
        target_month = hoy.month - i
        target_year = hoy.year
        while target_month <= 0:
            target_month += 12
            target_year -= 1
        
        _, last_day = monthrange(target_year, target_month)
        start = datetime(target_year, target_month, 1)
        end = datetime(target_year, target_month, last_day, 23, 59, 59)
        
        total = db.query(func.coalesce(func.sum(Purchase.total), 0)).filter(
            Purchase.lubricentro_id == lubricentro_id,
            Purchase.fecha >= start,
            Purchase.fecha <= end
        ).scalar()
        
        result.append({
            "date": start.strftime("%Y-%m"),
            "value": float(total or 0),
            "label": start.strftime("%b %Y")
        })
    
    return result
