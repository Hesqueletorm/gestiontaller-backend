"""
Endpoints de Facturación (Comprobantes/Sales)
"""
from typing import Any, List, Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.api import deps
from app.crud.crud_sale import sale as crud_sale
from app.schemas.sale_schema import (
    Sale, SaleCreate, SaleListItem, SaleFilter, NextNumberResponse
)
from app.models.client import Client as ClientModel, Visit as VisitModel

router = APIRouter()


@router.get("/", response_model=List[SaleListItem])
def read_sales(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    cliente: Optional[str] = Query(None, description="Filtrar por nombre de cliente"),
    vehiculo: Optional[str] = Query(None, description="Filtrar por descripción de vehículo"),
    desde: Optional[str] = Query(None, description="Fecha desde (YYYY-MM-DD)"),
    hasta: Optional[str] = Query(None, description="Fecha hasta (YYYY-MM-DD)"),
    current_user: Any = Depends(deps.get_current_user),
) -> Any:
    """
    Listar comprobantes con filtros opcionales.
    """
    filters = SaleFilter(
        cliente=cliente,
        vehiculo=vehiculo,
        desde=desde,
        hasta=hasta,
    )
    sales = crud_sale.get_filtered(
        db, 
        lubricentro_id=current_user.lubricentro_id,
        filters=filters, 
        skip=skip, 
        limit=limit
    )
    
    # Convertir a SaleListItem con descripción de vehículos
    result = []
    for s in sales:
        vehiculos_desc = " | ".join([v.descripcion for v in s.vehiculos]) if s.vehiculos else None
        result.append(SaleListItem(
            id=s.id,
            fecha=s.fecha,
            tipo=s.tipo,
            numero=f"{s.punto_venta}-{s.numero}",
            cliente_nombre=s.cliente_nombre,
            total=s.total,
            vehiculos_desc=vehiculos_desc,
        ))
    return result


@router.get("/next-number", response_model=NextNumberResponse)
def get_next_number(
    punto_venta: str = Query("0001", description="Punto de venta"),
    db: Session = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_user),
) -> Any:
    """
    Obtener el siguiente número de comprobante para un punto de venta.
    """
    # Normalizar punto de venta
    pv = punto_venta.zfill(4)[-4:]
    numero = crud_sale.get_next_number(db, punto_venta=pv)
    return NextNumberResponse(punto_venta=pv, numero=numero)


@router.get("/{sale_id}", response_model=Sale)
def read_sale(
    sale_id: int,
    db: Session = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_user),
) -> Any:
    """
    Obtener detalle de un comprobante por ID.
    """
    sale = crud_sale.get_with_details(db, id=sale_id)
    if not sale:
        raise HTTPException(status_code=404, detail="Comprobante no encontrado")
    return sale


@router.post("/", response_model=Sale)
def create_sale(
    *,
    db: Session = Depends(deps.get_db),
    sale_in: SaleCreate,
    current_user: Any = Depends(deps.get_current_user),
) -> Any:
    """
    Crear un nuevo comprobante (factura).
    Calcula automáticamente subtotal, IVA y total.
    Genera número automáticamente si no se especifica.
    """
    # Crear comprobante (asociado al lubricentro del usuario)
    sale = crud_sale.create(db, obj_in=sale_in, lubricentro_id=current_user.lubricentro_id)
    
    # Descontar stock de los items que tengan stock_id
    items_to_discount = [
        {"stock_id": item.stock_id, "cantidad": item.cantidad}
        for item in sale_in.items
        if hasattr(item, 'stock_id') and item.stock_id
    ]
    if items_to_discount:
        crud_sale.descontar_stock(db, items=items_to_discount)
    
    # Auto-crear visita para el cliente (si existe)
    if sale_in.cliente_nombre:
        cliente = None
        nombre_buscar = sale_in.cliente_nombre.strip()
        
        # Buscar cliente por nombre (case-insensitive, ignorando espacios extras)
        if nombre_buscar:
            cliente = db.query(ClientModel).filter(
                ClientModel.lubricentro_id == current_user.lubricentro_id,
                func.lower(func.trim(ClientModel.nombre)) == func.lower(nombre_buscar)
            ).first()
        
        # Si no existe por nombre, buscar por email
        if not cliente and hasattr(sale_in, 'cliente_email') and sale_in.cliente_email:
            email_buscar = sale_in.cliente_email.strip().lower()
            if email_buscar:
                cliente = db.query(ClientModel).filter(
                    ClientModel.lubricentro_id == current_user.lubricentro_id,
                    func.lower(ClientModel.email) == email_buscar
                ).first()
        
        # Si no existe por email, buscar por teléfono
        if not cliente and hasattr(sale_in, 'cliente_telefono') and sale_in.cliente_telefono:
            telefono_buscar = sale_in.cliente_telefono.strip()
            if telefono_buscar:
                cliente = db.query(ClientModel).filter(
                    ClientModel.lubricentro_id == current_user.lubricentro_id,
                    ClientModel.telefono == telefono_buscar
                ).first()
        
        # Si encontramos cliente, crear la visita
        if cliente:
            # Obtener info del vehículo y kilometraje
            vehiculo_desc = None
            kilometraje = 0
            if sale_in.vehiculos and len(sale_in.vehiculos) > 0:
                vehiculo_desc = sale_in.vehiculos[0].descripcion
                kilometraje = sale_in.vehiculos[0].kilometraje or 0
            
            # Crear registro de visita
            nueva_visita = VisitModel(
                cliente_id=cliente.id,
                comprobante_id=sale.id,
                fecha=sale.fecha or date.today().isoformat(),
                kilometraje=kilometraje,
                vehiculo_descripcion=vehiculo_desc,
                observacion=sale_in.observaciones if hasattr(sale_in, 'observaciones') else None,
                lubricentro_id=current_user.lubricentro_id
            )
            db.add(nueva_visita)
            db.commit()
    
    # Refrescar para obtener items y vehículos
    db.refresh(sale)
    return crud_sale.get_with_details(db, id=sale.id)
