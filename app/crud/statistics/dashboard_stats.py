"""
Estadísticas del Dashboard Principal
"""
from datetime import date, timedelta
from calendar import monthrange
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.sales import Sale
from app.models.purchase import Purchase
from app.models.client import Client
from app.models.inventory import Producto
from app.models.product_lote import ProductLote
from app.models.appointments import Appointment

from .sales_stats import get_monthly_sales_evolution
from .purchases_stats import get_monthly_purchases_evolution


def get_dashboard_stats(
    db: Session,
    lubricentro_id: int,
) -> dict:
    """Obtener estadísticas para dashboard principal"""
    hoy = date.today()
    mes_inicio = hoy.replace(day=1)
    
    # Mes anterior
    if mes_inicio.month == 1:
        mes_anterior_inicio = date(mes_inicio.year - 1, 12, 1)
    else:
        mes_anterior_inicio = date(mes_inicio.year, mes_inicio.month - 1, 1)
    _, last_day = monthrange(mes_anterior_inicio.year, mes_anterior_inicio.month)
    mes_anterior_fin = date(mes_anterior_inicio.year, mes_anterior_inicio.month, last_day)
    
    # Ventas mes actual
    ventas_mes = db.query(func.coalesce(func.sum(Sale.total), 0)).filter(
        Sale.lubricentro_id == lubricentro_id,
        Sale.fecha >= mes_inicio.isoformat()
    ).scalar() or 0
    
    # Ventas mes anterior
    ventas_anterior = db.query(func.coalesce(func.sum(Sale.total), 0)).filter(
        Sale.lubricentro_id == lubricentro_id,
        Sale.fecha >= mes_anterior_inicio.isoformat(),
        Sale.fecha <= mes_anterior_fin.isoformat()
    ).scalar() or 0
    
    # Compras mes actual
    compras_mes = db.query(func.coalesce(func.sum(Purchase.total), 0)).filter(
        Purchase.lubricentro_id == lubricentro_id,
        Purchase.fecha >= mes_inicio
    ).scalar() or 0
    
    # Compras mes anterior
    compras_anterior = db.query(func.coalesce(func.sum(Purchase.total), 0)).filter(
        Purchase.lubricentro_id == lubricentro_id,
        Purchase.fecha >= mes_anterior_inicio,
        Purchase.fecha <= mes_anterior_fin
    ).scalar() or 0
    
    # Variaciones
    var_ventas = ((ventas_mes - ventas_anterior) / ventas_anterior * 100) if ventas_anterior > 0 else 0
    var_compras = ((compras_mes - compras_anterior) / compras_anterior * 100) if compras_anterior > 0 else 0
    
    # Margen
    margen = ventas_mes - compras_mes
    margen_pct = (margen / ventas_mes * 100) if ventas_mes > 0 else 0
    
    # Clientes
    clientes_activos = db.query(func.count(Client.id)).filter(
        Client.lubricentro_id == lubricentro_id
    ).scalar() or 0
    
    clientes_nuevos = db.query(func.count(Client.id)).filter(
        Client.lubricentro_id == lubricentro_id,
        Client.fecha_registro >= mes_inicio.isoformat()
    ).scalar() or 0
    
    # Alertas inventario
    productos_alerta = db.query(func.count(Producto.id)).filter(
        Producto.lubricentro_id == lubricentro_id,
        Producto.alerta == 1
    ).scalar() or 0
    
    limite_vto = (hoy + timedelta(days=30)).isoformat()
    lotes_vencer = db.query(func.count(ProductLote.id)).filter(
        ProductLote.lubricentro_id == lubricentro_id,
        ProductLote.cantidad > 0,
        ProductLote.fecha_vencimiento.isnot(None),
        ProductLote.fecha_vencimiento <= limite_vto
    ).scalar() or 0
    
    # Turnos pendientes
    turnos_pendientes = db.query(func.count(Appointment.id)).filter(
        Appointment.lubricentro_id == lubricentro_id,
        Appointment.fecha >= hoy.isoformat()
    ).scalar() or 0
    
    # Evoluciones
    ventas_evol = get_monthly_sales_evolution(db, lubricentro_id, 6)
    compras_evol = get_monthly_purchases_evolution(db, lubricentro_id, 6)
    
    return {
        "ventas_mes": float(ventas_mes),
        "ventas_mes_anterior": float(ventas_anterior),
        "variacion_ventas": round(var_ventas, 1),
        "compras_mes": float(compras_mes),
        "compras_mes_anterior": float(compras_anterior),
        "variacion_compras": round(var_compras, 1),
        "margen_bruto": float(margen),
        "margen_porcentaje": round(margen_pct, 1),
        "clientes_activos": clientes_activos,
        "clientes_nuevos_mes": clientes_nuevos,
        "productos_alerta": productos_alerta,
        "lotes_por_vencer": lotes_vencer,
        "turnos_pendientes": turnos_pendientes,
        "ventas_ultimos_meses": ventas_evol,
        "compras_ultimos_meses": compras_evol,
    }
