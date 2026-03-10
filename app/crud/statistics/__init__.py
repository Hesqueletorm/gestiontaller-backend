"""
Constantes y utilidades compartidas para estadísticas
"""
from typing import Tuple
from datetime import date, timedelta

# Colores para gráficos
CHART_COLORS = [
    '#10B981',  # Esmeralda
    '#3B82F6',  # Azul
    '#F59E0B',  # Ámbar
    '#EF4444',  # Rojo
    '#8B5CF6',  # Violeta
    '#EC4899',  # Rosa
    '#06B6D4',  # Cyan
    '#84CC16',  # Lima
    '#F97316',  # Naranja
    '#6366F1',  # Indigo
]


def get_color(index: int) -> str:
    """Obtener color del palette cíclicamente"""
    return CHART_COLORS[index % len(CHART_COLORS)]


def get_date_range(period: str = "month", date_from: date = None, date_to: date = None) -> Tuple[date, date]:
    """Calcular rango de fechas según período"""
    hoy = date.today()
    
    if date_from and date_to:
        return date_from, date_to
    
    if period == "day":
        return hoy, hoy
    elif period == "week":
        start = hoy - timedelta(days=hoy.weekday())
        return start, hoy
    elif period == "month":
        start = hoy.replace(day=1)
        return start, hoy
    elif period == "year":
        start = hoy.replace(month=1, day=1)
        return start, hoy
    else:
        # Default: último mes
        start = hoy.replace(day=1)
        return start, hoy
