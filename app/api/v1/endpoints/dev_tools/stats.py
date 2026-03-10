"""
Endpoints de estadísticas para DevTools
"""
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api import deps
from app.models.user import User
from app.models.client import Client, Vehicle
from app.models.appointments import Appointment
from app.models.inventory import Producto, Service
from app.models.sales import Sale
from app.models.purchase import Purchase
from app.models.supplier import Supplier

router = APIRouter()


@router.get("/stats", response_model=dict)
def get_dev_stats(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Obtener estadísticas de la base de datos para el lubricentro actual.
    """
    lubri_id = current_user.lubricentro_id
    
    total_clientes = db.query(Client).filter(Client.lubricentro_id == lubri_id).count()
    total_vehiculos = db.query(Vehicle).join(Client).filter(Client.lubricentro_id == lubri_id).count()
    total_turnos = db.query(Appointment).filter(Appointment.lubricentro_id == lubri_id).count()
    total_productos = db.query(Producto).filter(Producto.lubricentro_id == lubri_id).count()
    total_ventas = db.query(Sale).filter(Sale.lubricentro_id == lubri_id).count()
    total_servicios = db.query(Service).filter(Service.lubricentro_id == lubri_id).count()
    total_compras = db.query(Purchase).filter(Purchase.lubricentro_id == lubri_id).count()
    total_proveedores = db.query(Supplier).filter(Supplier.lubricentro_id == lubri_id).count()
    
    return {
        "clientes": total_clientes,
        "vehiculos": total_vehiculos,
        "turnos": total_turnos,
        "productos": total_productos,
        "ventas": total_ventas,
        "servicios": total_servicios,
        "compras": total_compras,
        "proveedores": total_proveedores
    }
