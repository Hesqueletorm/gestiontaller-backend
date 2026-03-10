"""
Endpoints de escritura (POST/PUT/DELETE) de Clientes
"""
from typing import Any
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.api import deps
from app.schemas.client_schema import Client, ClientCreate, ClientUpdate, ClientSyncRequest
from app.models.client import Client as ClientModel, Vehicle as VehicleModel
from app.models.user import User

router = APIRouter()


@router.post("/", response_model=Client)
def create_client(
    *,
    db: Session = Depends(deps.get_db),
    client_in: ClientCreate,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """Crear nuevo cliente para el lubricentro actual."""
    db_client = ClientModel(
        lubricentro_id=current_user.lubricentro_id,
        nombre=client_in.nombre,
        email=client_in.email,
        telefono=client_in.telefono,
        direccion=client_in.direccion,
        notas=client_in.notas,
        fecha_registro=date.today().isoformat()
    )
    db.add(db_client)
    db.commit()
    db.refresh(db_client)
    return db_client


@router.post("/sync", response_model=Client)
def sync_client(
    *,
    db: Session = Depends(deps.get_db),
    client_in: ClientSyncRequest,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Sincronizar cliente: crear si no existe o actualizar si existe.
    Busca por nombre o email para detectar si ya existe.
    También sincroniza vehículos si se proporcionan.
    """
    existing_client = None
    
    # Buscar por email si existe
    if client_in.email:
        existing_client = db.query(ClientModel).filter(
            ClientModel.lubricentro_id == current_user.lubricentro_id,
            ClientModel.email == client_in.email
        ).first()
    
    # Si no encontró por email, buscar por nombre exacto
    if not existing_client and client_in.nombre:
        existing_client = db.query(ClientModel).filter(
            ClientModel.lubricentro_id == current_user.lubricentro_id,
            ClientModel.nombre == client_in.nombre
        ).first()
    
    if existing_client:
        # Actualizar cliente existente
        if client_in.nombre:
            existing_client.nombre = client_in.nombre
        if client_in.email:
            existing_client.email = client_in.email
        if client_in.telefono:
            existing_client.telefono = client_in.telefono
        if client_in.direccion:
            existing_client.direccion = client_in.direccion
        if client_in.notas:
            existing_client.notas = client_in.notas
        db.commit()
        db.refresh(existing_client)
        target_client = existing_client
    else:
        # Crear nuevo cliente con fecha de registro
        db_client = ClientModel(
            lubricentro_id=current_user.lubricentro_id,
            nombre=client_in.nombre,
            email=client_in.email,
            telefono=client_in.telefono,
            direccion=client_in.direccion,
            notas=client_in.notas,
            fecha_registro=date.today().isoformat()
        )
        db.add(db_client)
        db.commit()
        db.refresh(db_client)
        target_client = db_client
    
    # Sincronizar vehículos si se proporcionan
    if client_in.vehiculos:
        _sync_vehicles(db, target_client, client_in.vehiculos)
    
    return target_client


def _sync_vehicles(db: Session, target_client: ClientModel, vehiculos: list) -> None:
    """
    Función auxiliar para sincronizar vehículos de un cliente.
    """
    for v_data in vehiculos:
        # Buscar vehículo existente por patente (si tiene patente)
        existing_vehicle = None
        if v_data.patente and v_data.patente.strip():
            existing_vehicle = db.query(VehicleModel).filter(
                VehicleModel.cliente_id == target_client.id,
                func.lower(VehicleModel.patente) == v_data.patente.lower().strip()
            ).first()
        
        # Si no hay patente o no se encontró, buscar por descripción exacta
        if not existing_vehicle and v_data.descripcion:
            existing_vehicle = db.query(VehicleModel).filter(
                VehicleModel.cliente_id == target_client.id,
                VehicleModel.descripcion == v_data.descripcion
            ).first()
        
        if existing_vehicle:
            # Actualizar vehículo existente
            if v_data.descripcion:
                existing_vehicle.descripcion = v_data.descripcion
            if v_data.marca:
                existing_vehicle.marca = v_data.marca
            if v_data.version:
                existing_vehicle.version = v_data.version
            if v_data.modelo:
                existing_vehicle.modelo = v_data.modelo
            if v_data.patente:
                existing_vehicle.patente = v_data.patente.strip()
            if v_data.kilometraje and v_data.kilometraje > (existing_vehicle.kilometraje or 0):
                existing_vehicle.kilometraje = v_data.kilometraje
        else:
            # Crear nuevo vehículo
            descripcion = v_data.descripcion or f"{v_data.marca or ''} {v_data.version or ''} {v_data.modelo or ''} {v_data.patente or ''}".strip()
            if descripcion:  # Solo crear si hay alguna descripción
                new_vehicle = VehicleModel(
                    cliente_id=target_client.id,
                    descripcion=descripcion,
                    marca=v_data.marca,
                    version=v_data.version,
                    modelo=v_data.modelo,
                    patente=v_data.patente.strip() if v_data.patente else None,
                    kilometraje=v_data.kilometraje or 0
                )
                db.add(new_vehicle)
    
    db.commit()
    db.refresh(target_client)


@router.put("/{client_id}", response_model=Client)
def update_client(
    *,
    db: Session = Depends(deps.get_db),
    client_id: int,
    client_in: ClientUpdate,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """Actualizar cliente (solo si pertenece al lubricentro)."""
    client = db.query(ClientModel).filter(
        ClientModel.id == client_id,
        ClientModel.lubricentro_id == current_user.lubricentro_id
    ).first()
    if not client:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    update_data = client_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(client, field, value)
    
    db.commit()
    db.refresh(client)
    return client


@router.delete("/{client_id}")
def delete_client(
    *,
    db: Session = Depends(deps.get_db),
    client_id: int,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """Eliminar cliente y sus vehículos asociados."""
    client = db.query(ClientModel).filter(
        ClientModel.id == client_id,
        ClientModel.lubricentro_id == current_user.lubricentro_id
    ).first()
    if not client:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    db.delete(client)
    db.commit()
    return {"message": "Cliente eliminado correctamente", "id": client_id}
