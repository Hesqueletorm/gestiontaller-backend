"""
Endpoints para poblar inventario (productos, categorías, servicios)
"""
from typing import Any
import random
from datetime import timedelta, date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api import deps
from app.models.user import User
from app.models.inventory import Producto, Category, Service
from app.models.product_lote import ProductLote

from .schemas import DevToolResponse
from .catalogs import NOMBRES_STOCK, CATEGORIAS_STOCK, SERVICIOS_POR_CATEGORIA

router = APIRouter()


@router.post("/populate/inventory", response_model=DevToolResponse)
def populate_inventory(
    n: int = 50,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
) -> Any:
    """Generar productos de stock de prueba."""
    try:
        hoy = date.today()
        count = 0
        
        # Crear categorías base si no existen
        for cat_nombre in CATEGORIAS_STOCK:
            existe = db.query(Category).filter(
                Category.lubricentro_id == current_user.lubricentro_id,
                Category.nombre == cat_nombre
            ).first()
            if not existe:
                db.add(Category(lubricentro_id=current_user.lubricentro_id, nombre=cat_nombre))
        
        for _ in range(n):
            nombre = random.choice(NOMBRES_STOCK)
            codigo = f"P-{random.randint(10000, 99999)}"
            cantidad = round(random.uniform(1, 50), 2)
            categoria = random.choice(CATEGORIAS_STOCK)

            tiene_vto = random.random() < 0.7
            if tiene_vto:
                dias_delta = random.randint(-60, 365)
                fecha_vto = (hoy + timedelta(days=dias_delta)).isoformat()
                alerta = 1 if dias_delta <= 30 else 0
            else:
                fecha_vto = None
                alerta = 0

            ubic_a = f"A{random.randint(1,9)}" if random.random() < 0.8 else None
            ubic_b = f"B{random.randint(1,9)}" if random.random() < 0.4 else None
            ubic_c = f"C{random.randint(1,9)}" if random.random() < 0.2 else None

            producto = Producto(
                lubricentro_id=current_user.lubricentro_id,
                codigo=codigo,
                nombre=nombre,
                cantidad=cantidad,
                fecha_vencimiento=fecha_vto,
                alerta=alerta,
                ubicacion_a=ubic_a,
                ubicacion_b=ubic_b,
                ubicacion_c=ubic_c,
                categoria=categoria,
                descripcion="Producto generado por bot de desarrollo"
            )
            db.add(producto)
            db.flush()

            lote = ProductLote(
                lubricentro_id=current_user.lubricentro_id,
                producto_id=producto.id,
                cantidad=cantidad,
                fecha_vencimiento=fecha_vto
            )
            db.add(lote)
            count += 1
        
        db.commit()
        return DevToolResponse(success=True, message=f"✅ {count} productos generados con éxito", count=count)
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al generar productos: {str(e)}")


@router.post("/populate/services", response_model=DevToolResponse)
def populate_services(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
) -> Any:
    """Generar servicios de prueba organizados por categoría."""
    try:
        count = 0
        
        for categoria, servicios in SERVICIOS_POR_CATEGORIA.items():
            for servicio_nombre in servicios:
                existe = db.query(Service).filter(
                    Service.lubricentro_id == current_user.lubricentro_id,
                    Service.nombre == servicio_nombre
                ).first()
                
                if not existe:
                    precio = round(random.uniform(3000, 25000), 2)
                    servicio = Service(
                        lubricentro_id=current_user.lubricentro_id,
                        nombre=servicio_nombre,
                        categoria=categoria,
                        precio=precio,
                        activo=1
                    )
                    db.add(servicio)
                    count += 1
        
        db.commit()
        return DevToolResponse(success=True, message=f"✅ {count} servicios generados con éxito", count=count)
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al generar servicios: {str(e)}")
