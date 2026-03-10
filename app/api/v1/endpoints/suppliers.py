# Endpoints para gestión de Proveedores (ABM)
# Multi-tenant: aislado por lubricentro_id

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.api import deps
from app.models.user import User
from app.models.supplier import Supplier
from app.schemas.supplier_schema import (
    SupplierCreate, SupplierUpdate, SupplierResponse, 
    SupplierListResponse, SupplierSimple
)

router = APIRouter(prefix="/suppliers", tags=["Proveedores"])


@router.get("", response_model=SupplierListResponse)
def get_suppliers(
    page: int = Query(0, ge=0),
    page_size: int = Query(50, ge=1, le=100),
    search: Optional[str] = None,
    activo: Optional[bool] = None,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Obtener lista de proveedores del lubricentro con paginación y filtros
    """
    query = db.query(Supplier).filter(Supplier.lubricentro_id == current_user.lubricentro_id)
    
    # Filtro por estado activo
    if activo is not None:
        query = query.filter(Supplier.activo == activo)
    
    # Búsqueda por nombre, CUIT o contacto
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Supplier.nombre.ilike(search_term),
                Supplier.cuit.ilike(search_term),
                Supplier.contacto.ilike(search_term),
                Supplier.rubro.ilike(search_term)
            )
        )
    
    # Total antes de paginar
    total = query.count()
    
    # Ordenar y paginar
    suppliers = query.order_by(Supplier.nombre).offset(page * page_size).limit(page_size).all()
    
    return SupplierListResponse(
        items=suppliers,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/autocomplete", response_model=List[SupplierSimple])
def autocomplete_suppliers(
    q: str = Query("", min_length=0),
    limit: int = Query(20, ge=1, le=50),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Búsqueda de proveedores para autocompletado
    Retorna solo campos básicos para el desplegable
    """
    query = db.query(Supplier).filter(
        Supplier.lubricentro_id == current_user.lubricentro_id,
        Supplier.activo == True
    )
    
    if q:
        search_term = f"%{q}%"
        query = query.filter(
            or_(
                Supplier.nombre.ilike(search_term),
                Supplier.cuit.ilike(search_term)
            )
        )
    
    suppliers = query.order_by(Supplier.nombre).limit(limit).all()
    return suppliers


@router.get("/{supplier_id}", response_model=SupplierResponse)
def get_supplier(
    supplier_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Obtener un proveedor específico
    """
    supplier = db.query(Supplier).filter(
        Supplier.id == supplier_id,
        Supplier.lubricentro_id == current_user.lubricentro_id
    ).first()
    
    if not supplier:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")
    
    return supplier


@router.post("", response_model=SupplierResponse)
def create_supplier(
    data: SupplierCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Crear un nuevo proveedor
    """
    # Verificar que no exista un proveedor con el mismo nombre
    existing = db.query(Supplier).filter(
        Supplier.lubricentro_id == current_user.lubricentro_id,
        Supplier.nombre.ilike(data.nombre)
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=400, 
            detail=f"Ya existe un proveedor con el nombre '{data.nombre}'"
        )
    
    # Crear proveedor
    supplier = Supplier(
        lubricentro_id=current_user.lubricentro_id,
        **data.model_dump()
    )
    
    db.add(supplier)
    db.commit()
    db.refresh(supplier)
    
    return supplier


@router.put("/{supplier_id}", response_model=SupplierResponse)
def update_supplier(
    supplier_id: int,
    data: SupplierUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Actualizar un proveedor existente
    """
    supplier = db.query(Supplier).filter(
        Supplier.id == supplier_id,
        Supplier.lubricentro_id == current_user.lubricentro_id
    ).first()
    
    if not supplier:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")
    
    # Si se cambia el nombre, verificar que no exista otro con el mismo nombre
    if data.nombre and data.nombre.lower() != supplier.nombre.lower():
        existing = db.query(Supplier).filter(
            Supplier.lubricentro_id == current_user.lubricentro_id,
            Supplier.nombre.ilike(data.nombre),
            Supplier.id != supplier_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=400, 
                detail=f"Ya existe un proveedor con el nombre '{data.nombre}'"
            )
    
    # Actualizar campos
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(supplier, field, value)
    
    db.commit()
    db.refresh(supplier)
    
    return supplier


@router.delete("/{supplier_id}")
def delete_supplier(
    supplier_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Eliminar un proveedor (baja física)
    O usar PUT con activo=False para baja lógica
    """
    supplier = db.query(Supplier).filter(
        Supplier.id == supplier_id,
        Supplier.lubricentro_id == current_user.lubricentro_id
    ).first()
    
    if not supplier:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")
    
    db.delete(supplier)
    db.commit()
    
    return {"message": "Proveedor eliminado correctamente"}


@router.patch("/{supplier_id}/toggle-active")
def toggle_supplier_active(
    supplier_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Alternar estado activo/inactivo de un proveedor
    """
    supplier = db.query(Supplier).filter(
        Supplier.id == supplier_id,
        Supplier.lubricentro_id == current_user.lubricentro_id
    ).first()
    
    if not supplier:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")
    
    supplier.activo = not supplier.activo
    db.commit()
    
    return {
        "message": f"Proveedor {'activado' if supplier.activo else 'desactivado'} correctamente",
        "activo": supplier.activo
    }
