# Schemas Pydantic para módulo de Estadísticas
# Respuestas tipadas para endpoints de métricas

from pydantic import BaseModel
from typing import List, Optional
from datetime import date


# ============ MODELOS BASE ============

class ChartDataPoint(BaseModel):
    """Punto de datos genérico para gráficos"""
    label: str
    value: float
    color: Optional[str] = None


class TimeSeriesPoint(BaseModel):
    """Punto de datos para series temporales"""
    date: str
    value: float
    label: Optional[str] = None


class RankingItem(BaseModel):
    """Item de ranking (top productos, clientes, etc)"""
    id: Optional[int] = None
    name: str
    value: float
    quantity: Optional[float] = None
    percentage: Optional[float] = None


# ============ VENTAS ============

class SalesStats(BaseModel):
    """Estadísticas de ventas"""
    # KPIs principales
    total_facturacion: float
    total_comprobantes: int
    ticket_promedio: float
    total_iva: float
    
    # Evolución temporal
    evolucion_mensual: List[TimeSeriesPoint]
    
    # Distribuciones
    por_tipo_comprobante: List[ChartDataPoint]
    por_metodo_pago: List[ChartDataPoint]
    
    # Rankings
    top_productos: List[RankingItem]
    top_servicios: List[RankingItem]
    top_clientes: List[RankingItem]


# ============ COMPRAS ============

class PurchasesStats(BaseModel):
    """Estadísticas de compras a proveedores"""
    # KPIs principales
    total_compras: float
    cantidad_compras: int
    compra_promedio: float
    total_iva: float
    
    # Evolución temporal
    evolucion_mensual: List[TimeSeriesPoint]
    
    # Distribuciones
    por_proveedor: List[ChartDataPoint]
    por_metodo_pago: List[ChartDataPoint]
    
    # Rankings
    top_proveedores: List[RankingItem]
    top_productos_comprados: List[RankingItem]


# ============ CLIENTES ============

class ClientsStats(BaseModel):
    """Estadísticas de clientes"""
    # KPIs principales
    total_clientes: int
    clientes_nuevos_mes: int
    clientes_con_visitas: int
    frecuencia_promedio_dias: Optional[float] = None
    
    # Evolución temporal
    evolucion_nuevos: List[TimeSeriesPoint]
    evolucion_visitas: List[TimeSeriesPoint]
    
    # Rankings
    top_clientes_facturacion: List[RankingItem]
    top_clientes_visitas: List[RankingItem]


# ============ INVENTARIO ============

class InventoryStats(BaseModel):
    """Estadísticas de inventario"""
    # KPIs principales
    total_productos: int
    productos_con_stock: int
    productos_sin_stock: int
    productos_alerta_baja: int
    lotes_por_vencer: int
    
    # Distribuciones
    por_categoria: List[ChartDataPoint]
    stock_estado: List[ChartDataPoint]  # Con stock / Sin stock / Bajo
    
    # Ajustes
    ajustes_por_tipo: List[ChartDataPoint]
    evolucion_ajustes: List[TimeSeriesPoint]
    
    # Rankings
    productos_bajo_stock: List[RankingItem]
    lotes_proximos_vencer: List[RankingItem]


# ============ OPERACIONES ============

class OperationsStats(BaseModel):
    """Estadísticas de turnos y operaciones"""
    # KPIs principales
    turnos_mes: int
    turnos_hoy: int
    servicios_realizados: int
    
    # Distribuciones
    por_dia_semana: List[ChartDataPoint]
    por_hora: List[ChartDataPoint]
    por_servicio: List[ChartDataPoint]
    
    # Evolución
    evolucion_turnos: List[TimeSeriesPoint]


# ============ DASHBOARD GENERAL ============

class DashboardStats(BaseModel):
    """Resumen general para dashboard principal"""
    # Ventas
    ventas_mes: float
    ventas_mes_anterior: float
    variacion_ventas: float
    
    # Compras
    compras_mes: float
    compras_mes_anterior: float
    variacion_compras: float
    
    # Margen
    margen_bruto: float
    margen_porcentaje: float
    
    # Clientes
    clientes_activos: int
    clientes_nuevos_mes: int
    
    # Inventario
    productos_alerta: int
    lotes_por_vencer: int
    
    # Turnos
    turnos_pendientes: int
    
    # Gráficos resumen
    ventas_ultimos_meses: List[TimeSeriesPoint]
    compras_ultimos_meses: List[TimeSeriesPoint]


# ============ FILTROS ============

class DateRangeFilter(BaseModel):
    """Filtro de rango de fechas"""
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    period: Optional[str] = "month"  # day | week | month | year | custom
