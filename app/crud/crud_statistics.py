"""
CRUD para Estadísticas
Wrapper que mantiene la API existente usando módulos separados
"""
from datetime import date
from sqlalchemy.orm import Session

# Importar funciones de módulos especializados
from .statistics import get_color, get_date_range, CHART_COLORS
from .statistics.sales_stats import get_sales_stats, get_monthly_sales_evolution
from .statistics.purchases_stats import get_purchases_stats, get_monthly_purchases_evolution
from .statistics.clients_stats import get_clients_stats, get_monthly_new_clients_evolution, get_monthly_visits_evolution
from .statistics.inventory_stats import get_inventory_stats
from .statistics.operations_stats import get_operations_stats, get_monthly_appointments_evolution
from .statistics.dashboard_stats import get_dashboard_stats


class CRUDStatistics:
    """
    Operaciones CRUD para estadísticas del lubricentro
    Wrapper que mantiene compatibilidad con código existente
    """
    
    # ============ VENTAS ============
    
    def get_sales_stats(
        self,
        db: Session,
        lubricentro_id: int,
        date_from: date = None,
        date_to: date = None,
    ) -> dict:
        return get_sales_stats(db, lubricentro_id, date_from, date_to)
    
    def _get_monthly_sales_evolution(self, db: Session, lubricentro_id: int, months: int = 12):
        return get_monthly_sales_evolution(db, lubricentro_id, months)
    
    # ============ COMPRAS ============
    
    def get_purchases_stats(
        self,
        db: Session,
        lubricentro_id: int,
        date_from: date = None,
        date_to: date = None,
    ) -> dict:
        return get_purchases_stats(db, lubricentro_id, date_from, date_to)
    
    def _get_monthly_purchases_evolution(self, db: Session, lubricentro_id: int, months: int = 12):
        return get_monthly_purchases_evolution(db, lubricentro_id, months)
    
    # ============ CLIENTES ============
    
    def get_clients_stats(
        self,
        db: Session,
        lubricentro_id: int,
        date_from: date = None,
        date_to: date = None,
    ) -> dict:
        return get_clients_stats(db, lubricentro_id, date_from, date_to)
    
    def _get_monthly_new_clients_evolution(self, db: Session, lubricentro_id: int, months: int = 12):
        return get_monthly_new_clients_evolution(db, lubricentro_id, months)
    
    def _get_monthly_visits_evolution(self, db: Session, lubricentro_id: int, months: int = 12):
        return get_monthly_visits_evolution(db, lubricentro_id, months)
    
    # ============ INVENTARIO ============
    
    def get_inventory_stats(
        self,
        db: Session,
        lubricentro_id: int,
    ) -> dict:
        return get_inventory_stats(db, lubricentro_id)
    
    # ============ OPERACIONES ============
    
    def get_operations_stats(
        self,
        db: Session,
        lubricentro_id: int,
        date_from: date = None,
        date_to: date = None,
    ) -> dict:
        return get_operations_stats(db, lubricentro_id, date_from, date_to)
    
    def _get_monthly_appointments_evolution(self, db: Session, lubricentro_id: int, months: int = 12):
        return get_monthly_appointments_evolution(db, lubricentro_id, months)
    
    # ============ DASHBOARD ============
    
    def get_dashboard_stats(
        self,
        db: Session,
        lubricentro_id: int,
    ) -> dict:
        return get_dashboard_stats(db, lubricentro_id)


# Instancia global
statistics = CRUDStatistics()
