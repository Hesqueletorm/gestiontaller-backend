"""
Endpoints de Vehículos de Clientes
"""
from typing import Any, List
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.schemas.client_schema import Vehicle, VehicleCreate
from app.models.client import Client as ClientModel, Vehicle as VehicleModel, Visit as VisitModel
from app.models.user import User
from .schemas import VehicleKmUpdate

router = APIRouter()


@router.get("/{client_id}/vehicles", response_model=List[Vehicle])
def get_client_vehicles(
    client_id: int,
    only_active: bool = Query(True, description="Si es True, solo devuelve vehículos activos"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """Obtener vehículos de un cliente. Por defecto solo devuelve activos."""
    client = db.query(ClientModel).filter(
        ClientModel.id == client_id,
        ClientModel.lubricentro_id == current_user.lubricentro_id
    ).first()
    if not client:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    if only_active:
        return [v for v in client.vehiculos if v.activo]
    return client.vehiculos


@router.post("/{client_id}/vehicles", response_model=Vehicle)
def create_vehicle_for_client(
    *,
    db: Session = Depends(deps.get_db),
    client_id: int,
    vehicle_in: VehicleCreate,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """Crear vehículo para un cliente."""
    client = db.query(ClientModel).filter(
        ClientModel.id == client_id,
        ClientModel.lubricentro_id == current_user.lubricentro_id
    ).first()
    if not client:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    db_vehicle = VehicleModel(
        cliente_id=client_id,
        descripcion=vehicle_in.descripcion,
    )
    db.add(db_vehicle)
    db.commit()
    db.refresh(db_vehicle)
    return db_vehicle


@router.delete("/{client_id}/vehicles/{vehicle_id}")
def delete_vehicle(
    *,
    db: Session = Depends(deps.get_db),
    client_id: int,
    vehicle_id: int,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """Eliminar vehículo de un cliente."""
    client = db.query(ClientModel).filter(
        ClientModel.id == client_id,
        ClientModel.lubricentro_id == current_user.lubricentro_id
    ).first()
    if not client:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    vehicle = db.query(VehicleModel).filter(
        VehicleModel.id == vehicle_id,
        VehicleModel.cliente_id == client_id
    ).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehículo no encontrado")
    
    db.delete(vehicle)
    db.commit()
    return {"message": "Vehículo eliminado", "id": vehicle_id}


@router.patch("/{client_id}/vehicles/{vehicle_id}/toggle-active")
def toggle_vehicle_active(
    *,
    db: Session = Depends(deps.get_db),
    client_id: int,
    vehicle_id: int,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """Alternar estado activo/inactivo de un vehículo."""
    client = db.query(ClientModel).filter(
        ClientModel.id == client_id,
        ClientModel.lubricentro_id == current_user.lubricentro_id
    ).first()
    if not client:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    vehicle = db.query(VehicleModel).filter(
        VehicleModel.id == vehicle_id,
        VehicleModel.cliente_id == client_id
    ).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehículo no encontrado")
    
    vehicle.activo = not vehicle.activo
    db.commit()
    db.refresh(vehicle)
    
    return {
        "message": f"Vehículo {'activado' if vehicle.activo else 'desactivado'}",
        "id": vehicle_id,
        "activo": vehicle.activo
    }


@router.put("/{client_id}/vehicles", response_model=List[Vehicle])
def sync_vehicles(
    *,
    db: Session = Depends(deps.get_db),
    client_id: int,
    vehicles: List[VehicleCreate],
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Sincronizar todos los vehículos de un cliente.
    Elimina los existentes y crea los nuevos.
    """
    client = db.query(ClientModel).filter(
        ClientModel.id == client_id,
        ClientModel.lubricentro_id == current_user.lubricentro_id
    ).first()
    if not client:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    # Eliminar vehículos existentes
    db.query(VehicleModel).filter(VehicleModel.cliente_id == client_id).delete()
    
    # Crear nuevos
    new_vehicles = []
    for v in vehicles:
        if v.descripcion.strip():
            db_vehicle = VehicleModel(
                cliente_id=client_id,
                descripcion=v.descripcion.strip()
            )
            db.add(db_vehicle)
            new_vehicles.append(db_vehicle)
    
    db.commit()
    for v in new_vehicles:
        db.refresh(v)
    
    return new_vehicles


@router.put("/{client_id}/vehicles-km")
def update_vehicles_km(
    client_id: int,
    vehicles: List[VehicleKmUpdate],
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Actualizar el kilometraje de los vehículos del cliente.
    Actualiza la última visita del vehículo o crea una nueva.
    """
    client = db.query(ClientModel).filter(
        ClientModel.id == client_id,
        ClientModel.lubricentro_id == current_user.lubricentro_id
    ).first()
    if not client:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    today = datetime.now().strftime("%Y-%m-%d")
    
    for v in vehicles:
        if v.km is None or v.km == 0:
            continue
            
        # Buscar la última visita de este vehículo
        ultima_visita = db.query(VisitModel).filter(
            VisitModel.cliente_id == client_id,
            VisitModel.vehiculo_descripcion == v.descripcion
        ).order_by(VisitModel.fecha.desc()).first()
        
        if ultima_visita:
            ultima_visita.kilometraje = v.km
        else:
            nueva_visita = VisitModel(
                cliente_id=client_id,
                lubricentro_id=current_user.lubricentro_id,
                fecha=today,
                vehiculo_descripcion=v.descripcion,
                kilometraje=v.km,
                observacion="Actualización de kilometraje"
            )
            db.add(nueva_visita)
    
    db.commit()
    return {"message": "Kilometrajes actualizados correctamente"}
