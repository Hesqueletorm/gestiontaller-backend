"""
Endpoints de Compras (Ingreso de Stock)
"""
from typing import Any, List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.crud.crud_purchase import purchase as crud_purchase
from app.schemas.purchase_schema import (
    Purchase, PurchaseCreate, PurchaseBase,
    PurchaseListResponse, PurchaseStats
)

router = APIRouter()


@router.get("/", response_model=PurchaseListResponse)
def list_purchases(
    db: Session = Depends(deps.get_db),
    proveedor: Optional[str] = Query(None, description="Filtrar por proveedor"),
    fecha_desde: Optional[datetime] = Query(None, description="Fecha desde"),
    fecha_hasta: Optional[datetime] = Query(None, description="Fecha hasta"),
    page: int = Query(0, ge=0, description="Número de página (0-indexed)"),
    page_size: int = Query(25, ge=1, le=100, description="Items por página"),
    current_user: Any = Depends(deps.get_current_user),
) -> Any:
    """
    Listar compras con filtros y paginación.
    """
    if not current_user.lubricentro_id:
        raise HTTPException(status_code=400, detail="Usuario sin lubricentro asignado")
    
    skip = page * page_size
    purchases, total = crud_purchase.get_filtered(
        db,
        lubricentro_id=current_user.lubricentro_id,
        proveedor=proveedor,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        skip=skip,
        limit=page_size,
    )
    
    total_pages = (total + page_size - 1) // page_size if page_size > 0 else 1
    
    return PurchaseListResponse(
        items=purchases,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=max(total_pages, 1),
    )


@router.get("/stats", response_model=PurchaseStats)
def get_purchase_stats(
    db: Session = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_user),
) -> Any:
    """
    Obtener estadísticas de compras.
    """
    if not current_user.lubricentro_id:
        raise HTTPException(status_code=400, detail="Usuario sin lubricentro asignado")
    
    stats = crud_purchase.get_stats(db, lubricentro_id=current_user.lubricentro_id)
    return PurchaseStats(**stats)


@router.get("/proveedores", response_model=List[str])
def get_proveedores(
    db: Session = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_user),
) -> Any:
    """
    Obtener lista de proveedores únicos.
    """
    if not current_user.lubricentro_id:
        raise HTTPException(status_code=400, detail="Usuario sin lubricentro asignado")
    
    return crud_purchase.get_proveedores(db, lubricentro_id=current_user.lubricentro_id)


@router.get("/{purchase_id}", response_model=Purchase)
def get_purchase(
    purchase_id: int,
    db: Session = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_user),
) -> Any:
    """
    Obtener compra por ID con sus items.
    """
    purchase = crud_purchase.get_with_items(db, id=purchase_id)
    if not purchase:
        raise HTTPException(status_code=404, detail="Compra no encontrada")
    
    # Verificar que pertenece al lubricentro del usuario
    if purchase.lubricentro_id != current_user.lubricentro_id:
        raise HTTPException(status_code=403, detail="No tiene acceso a esta compra")
    
    return purchase


@router.post("/", response_model=Purchase)
def create_purchase(
    *,
    db: Session = Depends(deps.get_db),
    purchase_in: PurchaseCreate,
    current_user: Any = Depends(deps.get_current_user),
) -> Any:
    """
    Crear nueva compra e ingresar stock automáticamente.
    """
    if not current_user.lubricentro_id:
        raise HTTPException(status_code=400, detail="Usuario sin lubricentro asignado")
    
    if not purchase_in.items:
        raise HTTPException(status_code=400, detail="La compra debe tener al menos un item")
    
    purchase = crud_purchase.create_with_items(
        db,
        obj_in=purchase_in,
        lubricentro_id=current_user.lubricentro_id,
        user_id=current_user.id
    )
    return purchase


@router.delete("/{purchase_id}")
def delete_purchase(
    purchase_id: int,
    db: Session = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_user),
) -> Any:
    """
    Eliminar compra y revertir el stock ingresado.
    """
    purchase = crud_purchase.get(db, id=purchase_id)
    if not purchase:
        raise HTTPException(status_code=404, detail="Compra no encontrada")
    
    # Verificar pertenencia
    if purchase.lubricentro_id != current_user.lubricentro_id:
        raise HTTPException(status_code=403, detail="No tiene acceso a esta compra")
    
    # Solo admin puede eliminar
    if current_user.rol not in [1, 2]:
        raise HTTPException(status_code=403, detail="Solo administradores pueden eliminar compras")
    
    crud_purchase.delete_and_revert_stock(db, id=purchase_id)
    return {"ok": True, "message": "Compra eliminada y stock revertido"}
