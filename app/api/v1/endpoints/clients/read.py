"""
Endpoints de lectura (GET) de Clientes
"""
from typing import Any, List, Optional
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, func

from app.api import deps
from app.schemas.client_schema import (
    Client, Visit, ClientWithVisits, VehicleWithKm, VisitItemResumen
)
from app.models.client import (
    Client as ClientModel, 
    Vehicle as VehicleModel, 
    HistorialFactura, 
    Visit as VisitModel
)
from app.models.sales import SaleItem
from app.models.user import User
from .schemas import ClientListResponse

router = APIRouter()


@router.get("/", response_model=List[Client])
def read_clients(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """Listar todos los clientes del lubricentro actual."""
    clients = db.query(ClientModel).filter(
        ClientModel.lubricentro_id == current_user.lubricentro_id
    ).order_by(ClientModel.id.desc()).offset(skip).limit(limit).all()
    return clients


@router.get("/paginated", response_model=ClientListResponse)
def read_clients_paginated(
    db: Session = Depends(deps.get_db),
    q: Optional[str] = Query(None, description="Búsqueda por nombre, email, teléfono o vehículo"),
    fecha_visita_desde: Optional[str] = Query(None, description="Filtrar clientes con última visita desde esta fecha (YYYY-MM-DD)"),
    page: int = Query(0, ge=0, description="Número de página (0-indexed)"),
    page_size: int = Query(10, ge=1, le=100, description="Items por página"),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """Listar clientes con paginación, búsqueda y filtro por fecha de última visita."""
    query = db.query(ClientModel).filter(
        ClientModel.lubricentro_id == current_user.lubricentro_id
    )
    
    # Aplicar filtro de búsqueda si existe
    if q and q.strip():
        like_pattern = f"%{q}%"
        query = query.filter(
            or_(
                ClientModel.nombre.ilike(like_pattern),
                ClientModel.email.ilike(like_pattern),
                ClientModel.telefono.ilike(like_pattern),
                ClientModel.vehiculos.any(VehicleModel.descripcion.ilike(like_pattern))
            )
        )
    
    # Filtrar por fecha de última visita (desde)
    if fecha_visita_desde:
        subquery = db.query(
            VisitModel.cliente_id,
            func.max(VisitModel.fecha).label('ultima_fecha')
        ).group_by(VisitModel.cliente_id).subquery()
        
        query = query.join(subquery, ClientModel.id == subquery.c.cliente_id)
        query = query.filter(subquery.c.ultima_fecha >= fecha_visita_desde)
    
    # Contar total
    total = query.count()
    
    # Calcular páginas
    total_pages = (total + page_size - 1) // page_size if page_size > 0 else 1
    
    # Obtener items paginados
    skip = page * page_size
    clients = query.order_by(ClientModel.id.desc()).offset(skip).limit(page_size).all()
    
    return ClientListResponse(
        items=clients,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=max(total_pages, 1)
    )


@router.get("/search", response_model=List[Client])
def search_clients(
    q: str = Query("", description="Búsqueda por nombre, email, teléfono o vehículo"),
    db: Session = Depends(deps.get_db),
    limit: int = Query(50, le=100),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Buscar clientes por nombre, email, teléfono o descripción de vehículo.
    """
    if not q.strip():
        # Si no hay búsqueda, devolver todos
        return db.query(ClientModel).filter(
            ClientModel.lubricentro_id == current_user.lubricentro_id
        ).order_by(ClientModel.id.desc()).limit(limit).all()
    
    like_pattern = f"{q}%"
    
    # Buscar en clientes o en vehículos asociados
    clients = db.query(ClientModel).filter(
        ClientModel.lubricentro_id == current_user.lubricentro_id,
        or_(
            ClientModel.nombre.ilike(like_pattern),
            ClientModel.email.ilike(like_pattern),
            ClientModel.telefono.ilike(like_pattern),
            ClientModel.vehiculos.any(VehicleModel.descripcion.ilike(f"%{q}%"))
        )
    ).order_by(ClientModel.id.desc()).limit(limit).all()
    
    return clients


@router.get("/{client_id}", response_model=Client)
def read_client(
    *,
    db: Session = Depends(deps.get_db),
    client_id: int,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """Obtener cliente por ID (solo si pertenece al lubricentro)."""
    client = db.query(ClientModel).filter(
        ClientModel.id == client_id,
        ClientModel.lubricentro_id == current_user.lubricentro_id
    ).first()
    if not client:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return client


@router.get("/{client_id}/detail", response_model=ClientWithVisits)
def read_client_with_visits(
    *,
    db: Session = Depends(deps.get_db),
    client_id: int,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """Obtener cliente con historial de visitas."""
    client = db.query(ClientModel).filter(
        ClientModel.id == client_id,
        ClientModel.lubricentro_id == current_user.lubricentro_id
    ).first()
    if not client:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    # Obtener visitas ordenadas por fecha descendente
    visitas_db = db.query(VisitModel).filter(
        VisitModel.cliente_id == client_id
    ).order_by(VisitModel.fecha.desc()).all()
    
    # Extraer vehículos únicos con su último kilometraje
    vehiculos_data = {}
    
    # Construir visitas con productos y servicios
    visitas = []
    for visita in visitas_db:
        # Obtener productos y servicios del comprobante asociado
        productos = []
        servicios = []
        
        if visita.comprobante_id:
            items = db.query(SaleItem).filter(
                SaleItem.comprobante_id == visita.comprobante_id
            ).all()
            
            for item in items:
                item_resumen = VisitItemResumen(
                    articulo=item.articulo,
                    cantidad=item.cantidad,
                    precio_unitario=item.precio_unitario,
                    es_servicio=bool(item.es_servicio),
                    categoria=item.categoria
                )
                if item.es_servicio:
                    servicios.append(item_resumen)
                else:
                    productos.append(item_resumen)
        
        visitas.append(Visit(
            id=visita.id,
            cliente_id=visita.cliente_id,
            comprobante_id=visita.comprobante_id,
            fecha=visita.fecha,
            kilometraje=visita.kilometraje,
            vehiculo_descripcion=visita.vehiculo_descripcion,
            observacion=visita.observacion,
            productos=productos,
            servicios=servicios
        ))
        
        # Extraer vehículos para el resumen
        if visita.vehiculo_descripcion and visita.vehiculo_descripcion.strip():
            desc = visita.vehiculo_descripcion.strip()
            if desc not in vehiculos_data:
                vehiculos_data[desc] = {
                    "ultimo_km": visita.kilometraje,
                    "ultima_fecha": visita.fecha
                }
    
    # También agregar vehículos registrados del cliente
    for v in client.vehiculos:
        if v.descripcion not in vehiculos_data:
            vehiculos_data[v.descripcion] = {
                "ultimo_km": None,
                "ultima_fecha": None
            }
    
    # Construir lista de VehicleWithKm
    vehiculos_list = []
    temp_id = 1
    for desc, data in vehiculos_data.items():
        vehiculos_list.append(VehicleWithKm(
            id=temp_id,
            descripcion=desc,
            ultimo_km=data["ultimo_km"],
            ultima_fecha=data["ultima_fecha"]
        ))
        temp_id += 1
    
    return ClientWithVisits(
        id=client.id,
        nombre=client.nombre,
        email=client.email,
        telefono=client.telefono,
        direccion=client.direccion,
        notas=client.notas,
        vehiculos=vehiculos_list,
        visitas=visitas,
        total_visitas=len(visitas)
    )


@router.get("/{client_id}/visits", response_model=List[Visit])
def read_client_visits(
    *,
    db: Session = Depends(deps.get_db),
    client_id: int,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """Obtener historial de visitas de un cliente."""
    client = db.query(ClientModel).filter(
        ClientModel.id == client_id,
        ClientModel.lubricentro_id == current_user.lubricentro_id
    ).first()
    if not client:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    visitas = db.query(VisitModel).filter(
        VisitModel.cliente_id == client_id
    ).order_by(VisitModel.fecha.desc()).all()
    
    return visitas


@router.get("/{client_id}/history")
def get_client_history(
    client_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """Obtener historial de visitas/facturas de un cliente."""
    client = db.query(ClientModel).filter(
        ClientModel.id == client_id,
        ClientModel.lubricentro_id == current_user.lubricentro_id
    ).first()
    if not client:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    ultima = db.query(HistorialFactura).filter(
        HistorialFactura.cliente_id == client_id
    ).order_by(HistorialFactura.fecha.desc()).first()
    
    return {
        "ultima_visita": ultima.fecha if ultima else None,
        "total_visitas": len(client.historial_facturas)
    }
