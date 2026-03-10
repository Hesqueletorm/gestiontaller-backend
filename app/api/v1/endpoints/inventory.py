"""
Endpoints de Inventario (Productos y Categorías)
"""
from typing import Any, List, Optional
from datetime import date, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.crud.crud_inventory import product as crud_product, category as crud_category
from app.schemas.product_schema import (
    Product, ProductCreate, ProductUpdate,
    Category, CategoryCreate, CategoryUpdate,
    ProductListResponse
)

router = APIRouter()


# === PRODUCTOS ===

@router.get("/", response_model=ProductListResponse)
def read_products(
    db: Session = Depends(deps.get_db),
    nombre: Optional[str] = Query(None, description="Filtrar por nombre"),
    codigo: Optional[str] = Query(None, description="Filtrar por código"),
    categoria: Optional[str] = Query(None, description="Filtrar por categoría"),
    solo_alerta: bool = Query(False, description="Solo productos con alerta"),
    page: int = Query(0, ge=0, description="Número de página (0-indexed)"),
    page_size: int = Query(25, ge=1, le=100, description="Items por página"),
    current_user: Any = Depends(deps.get_current_user),
) -> Any:
    """
    Listar productos con filtros y paginación.
    """
    if not current_user.lubricentro_id:
        raise HTTPException(status_code=400, detail="Usuario sin lubricentro asignado")
    
    skip = page * page_size
    products, total = crud_product.get_filtered(
        db,
        lubricentro_id=current_user.lubricentro_id,
        nombre=nombre,
        codigo=codigo,
        categoria=categoria,
        solo_alerta=solo_alerta,
        skip=skip,
        limit=page_size,
    )
    
    # Debug: verificar datos de productos
    print(f"[DEBUG] Productos encontrados: {len(products)}, Total: {total}, Lubricentro: {current_user.lubricentro_id}")
    
    total_pages = (total + page_size - 1) // page_size if page_size > 0 else 1
    
    return ProductListResponse(
        items=products,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=max(total_pages, 1),
    )


@router.get("/autocomplete/search")
def autocomplete_products(
    q: str = Query("", description="Término de búsqueda"),
    db: Session = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_user),
) -> Any:
    """
    Autocomplete de productos para búsqueda rápida.
    Devuelve lista simple con id, nombre, codigo.
    """
    if not current_user.lubricentro_id:
        raise HTTPException(status_code=400, detail="Usuario sin lubricentro asignado")
    
    from app.models.inventory import Product as ProductModel
    from sqlalchemy import or_, func
    
    query = db.query(ProductModel).filter(
        ProductModel.lubricentro_id == current_user.lubricentro_id
    )
    
    if q:
        search_term = f"%{q}%"
        query = query.filter(
            or_(
                ProductModel.nombre.ilike(search_term),
                ProductModel.codigo.ilike(search_term)
            )
        )
    
    products = query.order_by(func.lower(ProductModel.nombre)).limit(50).all()
    
    return [
        {
            "id": p.id,
            "nombre": p.nombre,
            "codigo": p.codigo,
            "categoria": p.categoria,
            "tiene_vencimiento": p.tiene_vencimiento
        }
        for p in products
    ]


@router.get("/{product_id}", response_model=Product)
def read_product(
    product_id: int,
    db: Session = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_user),
) -> Any:
    """Obtener producto por ID."""
    product = crud_product.get(db, id=product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return product


@router.post("/", response_model=Product)
def create_product(
    *,
    db: Session = Depends(deps.get_db),
    product_in: ProductCreate,
    current_user: Any = Depends(deps.get_current_user),
) -> Any:
    """Crear nuevo producto."""
    if not current_user.lubricentro_id:
        raise HTTPException(status_code=400, detail="Usuario sin lubricentro asignado")
    
    # Crear producto con lubricentro_id del usuario actual
    from app.models.inventory import Product as ProductModel
    product_data = product_in.model_dump()
    product_data["lubricentro_id"] = current_user.lubricentro_id
    
    db_product = ProductModel(**product_data)
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product


@router.put("/{product_id}", response_model=Product)
def update_product(
    product_id: int,
    *,
    db: Session = Depends(deps.get_db),
    product_in: ProductUpdate,
    current_user: Any = Depends(deps.get_current_user),
) -> Any:
    """Actualizar producto."""
    product = crud_product.get(db, id=product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    product = crud_product.update(db, db_obj=product, obj_in=product_in)
    return product


@router.delete("/{product_id}")
def delete_product(
    product_id: int,
    db: Session = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_user),
) -> Any:
    """Eliminar producto."""
    product = crud_product.get(db, id=product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    crud_product.remove(db, id=product_id)
    return {"ok": True, "message": "Producto eliminado"}


# === CATEGORÍAS ===

@router.get("/categories/", response_model=List[Category])
def read_categories(
    db: Session = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_user),
) -> Any:
    """Listar todas las categorías."""
    return crud_category.get_multi(db, limit=500)


@router.get("/categories/names", response_model=List[str])
def read_category_names(
    db: Session = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_user),
) -> Any:
    """Obtener solo los nombres de categorías."""
    return crud_category.get_all_names(db)


@router.post("/categories/", response_model=Category)
def create_category(
    *,
    db: Session = Depends(deps.get_db),
    category_in: CategoryCreate,
    current_user: Any = Depends(deps.get_current_user),
) -> Any:
    """Crear nueva categoría."""
    # Verificar si ya existe
    existing = crud_category.get_by_name(db, name=category_in.nombre)
    if existing:
        raise HTTPException(status_code=400, detail="Ya existe una categoría con ese nombre")
    category = crud_category.create(db, obj_in=category_in)
    return category


@router.put("/categories/{category_id}", response_model=Category)
def update_category(
    category_id: int,
    *,
    db: Session = Depends(deps.get_db),
    category_in: CategoryUpdate,
    current_user: Any = Depends(deps.get_current_user),
) -> Any:
    """Actualizar categoría."""
    category = crud_category.get(db, id=category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    
    # Verificar nombre duplicado
    if category_in.nombre:
        existing = crud_category.get_by_name(db, name=category_in.nombre)
        if existing and existing.id != category_id:
            raise HTTPException(status_code=400, detail="Ya existe una categoría con ese nombre")
    
    category = crud_category.update(db, db_obj=category, obj_in=category_in)
    return category


@router.delete("/categories/{category_id}")
def delete_category(
    category_id: int,
    db: Session = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_user),
) -> Any:
    """Eliminar categoría (limpia productos asociados)."""
    category = crud_category.get(db, id=category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    crud_category.delete_and_update_products(db, db_obj=category)
    return {"ok": True, "message": "Categoría eliminada"}


# === ALERTAS DE VENCIMIENTO ===

@router.get("/alerts/expiring", response_model=List[Product])
def get_expiring_products(
    db: Session = Depends(deps.get_db),
    dias: int = Query(30, ge=0, le=365, description="Días para considerar próximo a vencer"),
    current_user: Any = Depends(deps.get_current_user_optional),
) -> Any:
    """
    Obtener productos próximos a vencer o ya vencidos.
    Incluye productos que vencen en los próximos X días y los ya vencidos.
    Filtrado por lubricentro del usuario (multi-tenant).
    
    Nota: La autenticación es opcional en este endpoint para soporte de cargas iniciales.
    """
    if not current_user or not current_user.lubricentro_id:
        # Si no hay usuario, devolver lista vacía en lugar de error
        return []
    
    products = crud_product.get_expiring(
        db, 
        lubricentro_id=current_user.lubricentro_id,
        dias=dias
    )
    return products


# === LOTES DE PRODUCTOS ===

from app.crud.crud_product_lote import product_lote as crud_lote
from app.schemas.product_lote_schema import ProductLote as ProductLoteSchema, ProductLoteListResponse

@router.get("/{product_id}/lotes", response_model=ProductLoteListResponse)
def get_product_lotes(
    product_id: int,
    db: Session = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_user),
) -> Any:
    """
    Obtener todos los lotes de un producto con stock disponible.
    Incluye información de estado de vencimiento para cada lote.
    """
    if not current_user.lubricentro_id:
        raise HTTPException(status_code=400, detail="Usuario sin lubricentro asignado")
    
    lotes = crud_lote.get_by_product(
        db,
        lubricentro_id=current_user.lubricentro_id,
        producto_id=product_id
    )
    
    # Enriquecer con información de vencimiento
    items = [crud_lote.enrich_with_vencimiento(lote) for lote in lotes]
    
    return ProductLoteListResponse(items=items, total=len(items))


# === AJUSTES DE STOCK ===

from datetime import datetime
from app.crud.crud_stock_adjustment import stock_adjustment as crud_adjustment
from app.schemas.stock_adjustment_schema import (
    StockAdjustment, StockAdjustmentCreate,
    StockAdjustmentListResponse, StockAdjustmentStats
)


@router.get("/adjustments/", response_model=StockAdjustmentListResponse)
def list_adjustments(
    db: Session = Depends(deps.get_db),
    producto_id: Optional[int] = Query(None, description="Filtrar por producto"),
    tipo_ajuste: Optional[str] = Query(None, description="Filtrar por tipo"),
    fecha_desde: Optional[datetime] = Query(None, description="Fecha desde"),
    fecha_hasta: Optional[datetime] = Query(None, description="Fecha hasta"),
    page: int = Query(0, ge=0, description="Número de página (0-indexed)"),
    page_size: int = Query(25, ge=1, le=100, description="Items por página"),
    current_user: Any = Depends(deps.get_current_user),
) -> Any:
    """Listar ajustes de stock con filtros y paginación."""
    if not current_user.lubricentro_id:
        raise HTTPException(status_code=400, detail="Usuario sin lubricentro asignado")
    
    skip = page * page_size
    items, total = crud_adjustment.get_filtered(
        db,
        lubricentro_id=current_user.lubricentro_id,
        producto_id=producto_id,
        tipo_ajuste=tipo_ajuste,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        skip=skip,
        limit=page_size,
    )
    
    total_pages = (total + page_size - 1) // page_size if page_size > 0 else 1
    
    return StockAdjustmentListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=max(total_pages, 1),
    )


@router.post("/adjustments/", response_model=StockAdjustment)
def create_adjustment(
    *,
    db: Session = Depends(deps.get_db),
    adjustment_in: StockAdjustmentCreate,
    current_user: Any = Depends(deps.get_current_user),
) -> Any:
    """
    Crear ajuste de stock (reduce cantidad del producto).
    Tipos válidos: vencimiento, descarte, consumo_interno
    """
    if not current_user.lubricentro_id:
        raise HTTPException(status_code=400, detail="Usuario sin lubricentro asignado")
    
    try:
        adjustment = crud_adjustment.create_and_adjust_stock(
            db,
            obj_in=adjustment_in,
            lubricentro_id=current_user.lubricentro_id,
            user_id=current_user.id
        )
        return adjustment
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/adjustments/stats", response_model=StockAdjustmentStats)
def get_adjustment_stats(
    db: Session = Depends(deps.get_db),
    current_user: Any = Depends(deps.get_current_user),
) -> Any:
    """Obtener estadísticas de ajustes por tipo."""
    if not current_user.lubricentro_id:
        raise HTTPException(status_code=400, detail="Usuario sin lubricentro asignado")
    
    stats = crud_adjustment.get_stats(db, lubricentro_id=current_user.lubricentro_id)
    return StockAdjustmentStats(**stats)
