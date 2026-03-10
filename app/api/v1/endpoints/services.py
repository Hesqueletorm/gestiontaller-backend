# Endpoints CRUD para Servicios

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.api import deps
from app.models.inventory import Servicio
from app.models.user import User
from app.schemas.service_schema import Service, ServiceCreate, ServiceUpdate
from app.api.deps import get_current_user

router = APIRouter()


@router.get("/", response_model=List[Service])
def get_services(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    categoria: Optional[str] = None,
    activo: Optional[int] = Query(1, description="1=activos, 0=inactivos, None=todos"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtener lista de servicios del lubricentro"""
    query = db.query(Servicio).filter(Servicio.lubricentro_id == current_user.lubricentro_id)
    
    if activo is not None:
        query = query.filter(Servicio.activo == activo)
    
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (Servicio.nombre.ilike(search_term)) | 
            (Servicio.codigo.ilike(search_term)) |
            (Servicio.descripcion.ilike(search_term))
        )
    
    if categoria:
        query = query.filter(Servicio.categoria == categoria)
    
    return query.order_by(Servicio.nombre).offset(skip).limit(limit).all()


@router.get("/categorias")
def get_service_categories(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtener categorías únicas de servicios"""
    categorias = db.query(Servicio.categoria).filter(
        Servicio.lubricentro_id == current_user.lubricentro_id,
        Servicio.categoria.isnot(None),
        Servicio.categoria != ""
    ).distinct().all()
    
    return [c[0] for c in categorias if c[0]]


@router.get("/{service_id}", response_model=Service)
def get_service(
    service_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtener un servicio por ID"""
    service = db.query(Servicio).filter(
        Servicio.id == service_id,
        Servicio.lubricentro_id == current_user.lubricentro_id
    ).first()
    
    if not service:
        raise HTTPException(status_code=404, detail="Servicio no encontrado")
    
    return service


@router.post("/", response_model=Service, status_code=status.HTTP_201_CREATED)
def create_service(
    service_data: ServiceCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(get_current_user)
):
    """Crear un nuevo servicio"""
    new_service = Servicio(
        lubricentro_id=current_user.lubricentro_id,
        codigo=service_data.codigo,
        nombre=service_data.nombre,
        descripcion=service_data.descripcion,
        precio=service_data.precio,
        categoria=service_data.categoria,
        activo=service_data.activo
    )
    
    db.add(new_service)
    db.commit()
    db.refresh(new_service)
    
    return new_service


@router.put("/{service_id}", response_model=Service)
def update_service(
    service_id: int,
    service_data: ServiceUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(get_current_user)
):
    """Actualizar un servicio"""
    service = db.query(Servicio).filter(
        Servicio.id == service_id,
        Servicio.lubricentro_id == current_user.lubricentro_id
    ).first()
    
    if not service:
        raise HTTPException(status_code=404, detail="Servicio no encontrado")
    
    update_data = service_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(service, field, value)
    
    db.commit()
    db.refresh(service)
    
    return service


@router.delete("/{service_id}")
def delete_service(
    service_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(get_current_user)
):
    """Eliminar un servicio (soft delete - marcar como inactivo)"""
    service = db.query(Servicio).filter(
        Servicio.id == service_id,
        Servicio.lubricentro_id == current_user.lubricentro_id
    ).first()
    
    if not service:
        raise HTTPException(status_code=404, detail="Servicio no encontrado")
    
    # Soft delete
    service.activo = 0
    db.commit()
    
    return {"message": "Servicio eliminado correctamente"}


@router.delete("/{service_id}/permanent")
def delete_service_permanent(
    service_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(get_current_user)
):
    """Eliminar un servicio permanentemente"""
    service = db.query(Servicio).filter(
        Servicio.id == service_id,
        Servicio.lubricentro_id == current_user.lubricentro_id
    ).first()
    
    if not service:
        raise HTTPException(status_code=404, detail="Servicio no encontrado")
    
    db.delete(service)
    db.commit()
    
    return {"message": "Servicio eliminado permanentemente"}
