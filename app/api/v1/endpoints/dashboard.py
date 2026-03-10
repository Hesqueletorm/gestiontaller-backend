"""
Endpoints del Dashboard - Estadísticas
"""
from typing import Any, List, Optional
from datetime import date, timedelta, datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from pydantic import BaseModel

from app.api import deps
from app.models.sales import Sale, SaleItem
from app.models.client import Client as ClientModel, Visit as VisitModel
from app.models.inventory import Product
from app.models.appointments import Appointment
from app.models.user import User

router = APIRouter()


# === SCHEMAS ===

class DashboardStats(BaseModel):
    ventas_totales: float
    ventas_hoy: float
    ventas_mes: float
    clientes_frecuentes: int
    clientes_nuevos: int
    productos_vencidos_hoy: int
    productos_vencidos_semana: int
    turnos_hoy: int


class VentaReciente(BaseModel):
    id: int
    fecha: str
    cliente: str
    total: float
    tipo: str


class TurnoHoy(BaseModel):
    id: int
    hora: str
    cliente: str
    servicio: str
    vehiculo: str


class DashboardData(BaseModel):
    stats: DashboardStats
    ventas_recientes: List[VentaReciente]
    turnos_hoy: List[TurnoHoy]


# === ENDPOINTS ===

@router.get("/stats", response_model=DashboardData)
def get_dashboard_stats(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Obtener estadísticas del dashboard.
    """
    lubricentro_id = current_user.lubricentro_id
    today = date.today()
    start_of_month = today.replace(day=1)
    start_of_week = today - timedelta(days=today.weekday())
    end_of_week = start_of_week + timedelta(days=6)
    
    # === VENTAS ===
    # Ventas totales (todo el tiempo)
    ventas_totales = db.query(func.coalesce(func.sum(Sale.total), 0)).filter(
        Sale.lubricentro_id == lubricentro_id
    ).scalar() or 0
    
    # Ventas de hoy
    ventas_hoy = db.query(func.coalesce(func.sum(Sale.total), 0)).filter(
        Sale.lubricentro_id == lubricentro_id,
        Sale.fecha == today.strftime("%Y-%m-%d")
    ).scalar() or 0
    
    # Ventas del mes
    ventas_mes = db.query(func.coalesce(func.sum(Sale.total), 0)).filter(
        Sale.lubricentro_id == lubricentro_id,
        Sale.fecha >= start_of_month.strftime("%Y-%m-%d")
    ).scalar() or 0
    
    # === CLIENTES ===
    # Clientes frecuentes (con más de 2 visitas)
    # Primero obtenemos los clientes con sus conteos de visitas
    try:
        subquery = db.query(
            VisitModel.cliente_id,
            func.count(VisitModel.id).label('visit_count')
        ).group_by(VisitModel.cliente_id).having(func.count(VisitModel.id) > 2).subquery()
        
        clientes_frecuentes = db.query(func.count()).select_from(subquery).scalar() or 0
    except Exception:
        clientes_frecuentes = 0
    
    # Clientes nuevos (creados este mes)
    try:
        clientes_nuevos = db.query(func.count(ClientModel.id)).filter(
            ClientModel.lubricentro_id == lubricentro_id,
            ClientModel.fecha_registro >= start_of_month.strftime("%Y-%m-%d")
        ).scalar() or 0
    except Exception:
        clientes_nuevos = 0
    
    # === PRODUCTOS VENCIDOS ===
    # Productos vencidos hoy
    try:
        productos_vencidos_hoy = db.query(func.count(Product.id)).filter(
            Product.fecha_vencimiento == today.strftime("%Y-%m-%d")
        ).scalar() or 0
    except Exception:
        productos_vencidos_hoy = 0
    
    # Productos vencidos esta semana
    try:
        productos_vencidos_semana = db.query(func.count(Product.id)).filter(
            Product.fecha_vencimiento >= start_of_week.strftime("%Y-%m-%d"),
            Product.fecha_vencimiento <= end_of_week.strftime("%Y-%m-%d")
        ).scalar() or 0
    except Exception:
        productos_vencidos_semana = 0
    
    # === TURNOS HOY ===
    try:
        turnos_hoy_count = db.query(func.count(Appointment.id)).filter(
            Appointment.lubricentro_id == lubricentro_id,
            Appointment.fecha == today.strftime("%Y-%m-%d")
        ).scalar() or 0
    except Exception:
        turnos_hoy_count = 0
    
    # === VENTAS RECIENTES ===
    try:
        ventas_recientes_db = db.query(Sale).filter(
            Sale.lubricentro_id == lubricentro_id
        ).order_by(Sale.id.desc()).limit(10).all()
        
        ventas_recientes = [
            VentaReciente(
                id=v.id,
                fecha=v.fecha,
                cliente=v.cliente_nombre,
                total=v.total,
                tipo=v.tipo
            )
            for v in ventas_recientes_db
        ]
    except Exception:
        ventas_recientes = []
    
    # === TURNOS DE HOY DETALLADOS ===
    try:
        turnos_hoy_db = db.query(Appointment).filter(
            Appointment.lubricentro_id == lubricentro_id,
            Appointment.fecha == today.strftime("%Y-%m-%d")
        ).order_by(Appointment.hora).all()
        
        turnos_hoy_list = [
            TurnoHoy(
                id=t.id,
                hora=t.hora or "Sin hora",
                cliente=t.cliente or "Sin cliente",
                servicio=t.servicio or "Servicio general",
                vehiculo=t.vehiculo or ""
            )
            for t in turnos_hoy_db
        ]
    except Exception:
        turnos_hoy_list = []
    
    return DashboardData(
        stats=DashboardStats(
            ventas_totales=float(ventas_totales),
            ventas_hoy=float(ventas_hoy),
            ventas_mes=float(ventas_mes),
            clientes_frecuentes=clientes_frecuentes,
            clientes_nuevos=clientes_nuevos,
            productos_vencidos_hoy=productos_vencidos_hoy,
            productos_vencidos_semana=productos_vencidos_semana,
            turnos_hoy=turnos_hoy_count,
        ),
        ventas_recientes=ventas_recientes,
        turnos_hoy=turnos_hoy_list,
    )
