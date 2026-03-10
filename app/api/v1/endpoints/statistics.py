"""
Endpoints de Estadísticas
Dashboard y métricas para gestión del lubricentro
"""
from typing import Any, Optional
from datetime import date
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.crud.crud_statistics import statistics as crud_stats
from app.schemas.statistics_schema import (
    SalesStats, PurchasesStats, ClientsStats,
    InventoryStats, OperationsStats, DashboardStats
)

router = APIRouter()


@router.get("/dashboard", response_model=DashboardStats)
def get_dashboard(
    db: Session = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_user),
) -> Any:
    """
    Obtener estadísticas del dashboard principal.
    Resumen general de KPIs clave del lubricentro.
    """
    if not current_user.lubricentro_id:
        return DashboardStats(
            ventas_mes=0, ventas_mes_anterior=0, variacion_ventas=0,
            compras_mes=0, compras_mes_anterior=0, variacion_compras=0,
            margen_bruto=0, margen_porcentaje=0,
            clientes_activos=0, clientes_nuevos_mes=0,
            productos_alerta=0, lotes_por_vencer=0, turnos_pendientes=0,
            ventas_ultimos_meses=[], compras_ultimos_meses=[]
        )
    
    return crud_stats.get_dashboard_stats(db, lubricentro_id=current_user.lubricentro_id)


@router.get("/sales", response_model=SalesStats)
def get_sales_statistics(
    db: Session = Depends(deps.get_db),
    date_from: Optional[date] = Query(None, description="Fecha desde (YYYY-MM-DD)"),
    date_to: Optional[date] = Query(None, description="Fecha hasta (YYYY-MM-DD)"),
    current_user: Any = Depends(deps.get_current_user),
) -> Any:
    """
    Obtener estadísticas de ventas.
    Incluye facturación, métodos de pago, top productos y evolución.
    """
    if not current_user.lubricentro_id:
        return SalesStats(
            total_facturacion=0, total_comprobantes=0, ticket_promedio=0, total_iva=0,
            evolucion_mensual=[], por_tipo_comprobante=[], por_metodo_pago=[],
            top_productos=[], top_servicios=[], top_clientes=[]
        )
    
    return crud_stats.get_sales_stats(
        db,
        lubricentro_id=current_user.lubricentro_id,
        date_from=date_from,
        date_to=date_to
    )


@router.get("/purchases", response_model=PurchasesStats)
def get_purchases_statistics(
    db: Session = Depends(deps.get_db),
    date_from: Optional[date] = Query(None, description="Fecha desde (YYYY-MM-DD)"),
    date_to: Optional[date] = Query(None, description="Fecha hasta (YYYY-MM-DD)"),
    current_user: Any = Depends(deps.get_current_user),
) -> Any:
    """
    Obtener estadísticas de compras a proveedores.
    Incluye gastos, proveedores, productos y evolución.
    """
    if not current_user.lubricentro_id:
        return PurchasesStats(
            total_compras=0, cantidad_compras=0, compra_promedio=0, total_iva=0,
            evolucion_mensual=[], por_proveedor=[], por_metodo_pago=[],
            top_proveedores=[], top_productos_comprados=[]
        )
    
    return crud_stats.get_purchases_stats(
        db,
        lubricentro_id=current_user.lubricentro_id,
        date_from=date_from,
        date_to=date_to
    )


@router.get("/clients", response_model=ClientsStats)
def get_clients_statistics(
    db: Session = Depends(deps.get_db),
    date_from: Optional[date] = Query(None, description="Fecha desde (YYYY-MM-DD)"),
    date_to: Optional[date] = Query(None, description="Fecha hasta (YYYY-MM-DD)"),
    current_user: Any = Depends(deps.get_current_user),
) -> Any:
    """
    Obtener estadísticas de clientes.
    Incluye total, nuevos, frecuencia y top clientes.
    """
    if not current_user.lubricentro_id:
        return ClientsStats(
            total_clientes=0, clientes_nuevos_mes=0, clientes_con_visitas=0,
            frecuencia_promedio_dias=None,
            evolucion_nuevos=[], evolucion_visitas=[],
            top_clientes_facturacion=[], top_clientes_visitas=[]
        )
    
    return crud_stats.get_clients_stats(
        db,
        lubricentro_id=current_user.lubricentro_id,
        date_from=date_from,
        date_to=date_to
    )


@router.get("/inventory", response_model=InventoryStats)
def get_inventory_statistics(
    db: Session = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_user),
) -> Any:
    """
    Obtener estadísticas de inventario.
    Incluye stock, categorías, vencimientos y ajustes.
    """
    if not current_user.lubricentro_id:
        return InventoryStats(
            total_productos=0, productos_con_stock=0, productos_sin_stock=0,
            productos_alerta_baja=0, lotes_por_vencer=0,
            por_categoria=[], stock_estado=[], ajustes_por_tipo=[],
            evolucion_ajustes=[], productos_bajo_stock=[], lotes_proximos_vencer=[]
        )
    
    return crud_stats.get_inventory_stats(db, lubricentro_id=current_user.lubricentro_id)


@router.get("/operations", response_model=OperationsStats)
def get_operations_statistics(
    db: Session = Depends(deps.get_db),
    date_from: Optional[date] = Query(None, description="Fecha desde (YYYY-MM-DD)"),
    date_to: Optional[date] = Query(None, description="Fecha hasta (YYYY-MM-DD)"),
    current_user: Any = Depends(deps.get_current_user),
) -> Any:
    """
    Obtener estadísticas de turnos y operaciones.
    Incluye distribución horaria, servicios y evolución.
    """
    if not current_user.lubricentro_id:
        return OperationsStats(
            turnos_mes=0, turnos_hoy=0, servicios_realizados=0,
            por_dia_semana=[], por_hora=[], por_servicio=[],
            evolucion_turnos=[]
        )
    
    return crud_stats.get_operations_stats(
        db,
        lubricentro_id=current_user.lubricentro_id,
        date_from=date_from,
        date_to=date_to
    )
