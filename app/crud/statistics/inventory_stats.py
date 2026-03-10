"""
Estadísticas de Inventario
"""
from datetime import date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.models.inventory import Producto, StockAdjustment
from app.models.product_lote import ProductLote
from . import get_color


def get_inventory_stats(
    db: Session,
    lubricentro_id: int,
) -> dict:
    """Obtener estadísticas de inventario"""
    hoy = date.today()
    limite_vencimiento = (hoy + timedelta(days=30)).isoformat()
    
    # Productos totales
    total_productos = db.query(func.count(Producto.id)).filter(
        Producto.lubricentro_id == lubricentro_id
    ).scalar() or 0
    
    # Productos con stock
    con_stock = db.query(func.count(Producto.id)).filter(
        Producto.lubricentro_id == lubricentro_id,
        Producto.cantidad > 0
    ).scalar() or 0
    
    # Productos sin stock
    sin_stock = total_productos - con_stock
    
    # Productos con alerta
    con_alerta = db.query(func.count(Producto.id)).filter(
        Producto.lubricentro_id == lubricentro_id,
        Producto.alerta == 1
    ).scalar() or 0
    
    # Lotes por vencer
    lotes_por_vencer = db.query(func.count(ProductLote.id)).filter(
        ProductLote.lubricentro_id == lubricentro_id,
        ProductLote.cantidad > 0,
        ProductLote.fecha_vencimiento.isnot(None),
        ProductLote.fecha_vencimiento != "",
        ProductLote.fecha_vencimiento <= limite_vencimiento
    ).scalar() or 0
    
    # Por categoría
    por_categoria = db.query(
        Producto.categoria,
        func.count(Producto.id).label('cantidad')
    ).filter(
        Producto.lubricentro_id == lubricentro_id,
        Producto.categoria.isnot(None),
        Producto.categoria != ""
    ).group_by(Producto.categoria).order_by(desc('cantidad')).all()
    
    # Ajustes por tipo
    ajustes_tipo = db.query(
        StockAdjustment.tipo_ajuste,
        func.count(StockAdjustment.id).label('cantidad'),
        func.sum(StockAdjustment.cantidad).label('total')
    ).filter(
        StockAdjustment.lubricentro_id == lubricentro_id
    ).group_by(StockAdjustment.tipo_ajuste).all()
    
    # Productos bajo stock (con cantidad < 5)
    bajo_stock = db.query(
        Producto.nombre,
        Producto.cantidad
    ).filter(
        Producto.lubricentro_id == lubricentro_id,
        Producto.cantidad > 0,
        Producto.cantidad < 5
    ).order_by(Producto.cantidad.asc()).limit(10).all()
    
    return {
        "total_productos": total_productos,
        "productos_con_stock": con_stock,
        "productos_sin_stock": sin_stock,
        "productos_alerta_baja": con_alerta,
        "lotes_por_vencer": lotes_por_vencer,
        "por_categoria": [
            {"label": r.categoria or "Sin categoría", "value": float(r.cantidad), "color": get_color(i)}
            for i, r in enumerate(por_categoria)
        ],
        "stock_estado": [
            {"label": "Con Stock", "value": float(con_stock), "color": "#10B981"},
            {"label": "Sin Stock", "value": float(sin_stock), "color": "#EF4444"},
        ],
        "ajustes_por_tipo": [
            {"label": r.tipo_ajuste.replace("_", " ").title(), "value": float(r.total or 0), "color": get_color(i)}
            for i, r in enumerate(ajustes_tipo)
        ],
        "evolucion_ajustes": [],
        "productos_bajo_stock": [
            {"name": r.nombre, "value": float(r.cantidad), "quantity": float(r.cantidad)}
            for r in bajo_stock
        ],
        "lotes_proximos_vencer": [],
    }
