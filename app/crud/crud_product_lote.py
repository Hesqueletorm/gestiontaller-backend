"""
CRUD operations para ProductLote (Lotes de productos)
"""
from typing import List, Optional, Tuple
from datetime import date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.product_lote import ProductLote
from app.models.inventory import Producto
from app.schemas.product_lote_schema import ProductLoteCreate, ProductLoteUpdate


def calcular_estado_vencimiento(fecha_vencimiento: Optional[str]) -> dict:
    """Calcula el estado de vencimiento de un lote"""
    if not fecha_vencimiento:
        return {"estado": "none", "dias": None, "texto": "Sin vencimiento"}
    
    try:
        hoy = date.today()
        vto = date.fromisoformat(fecha_vencimiento)
        dias = (vto - hoy).days
        
        if dias > 30:
            return {"estado": "ok", "dias": dias, "texto": f"Vence en {dias} días"}
        elif dias > 0:
            return {"estado": "warning", "dias": dias, "texto": f"Vence en {dias} días"}
        elif dias == 0:
            return {"estado": "warning", "dias": 0, "texto": "Vence hoy"}
        else:
            return {"estado": "expired", "dias": abs(dias), "texto": f"Vencido hace {abs(dias)} días"}
    except:
        return {"estado": "none", "dias": None, "texto": "Fecha inválida"}


class CRUDProductLote:
    
    def get_by_product(
        self,
        db: Session,
        *,
        lubricentro_id: int,
        producto_id: int,
        include_empty: bool = False
    ) -> List[ProductLote]:
        """
        Obtener todos los lotes de un producto.
        Por defecto solo retorna lotes con cantidad > 0.
        Ordenados por fecha de vencimiento (más próximo primero).
        """
        query = db.query(ProductLote).filter(
            ProductLote.lubricentro_id == lubricentro_id,
            ProductLote.producto_id == producto_id
        )
        
        if not include_empty:
            query = query.filter(ProductLote.cantidad > 0)
        
        # Ordenar por vencimiento (NULL al final)
        return query.order_by(
            ProductLote.fecha_vencimiento.asc().nullslast()
        ).all()
    
    def get_by_id(self, db: Session, *, lote_id: int) -> Optional[ProductLote]:
        """Obtener lote por ID"""
        return db.query(ProductLote).filter(ProductLote.id == lote_id).first()
    
    def create(
        self,
        db: Session,
        *,
        lubricentro_id: int,
        obj_in: ProductLoteCreate
    ) -> ProductLote:
        """Crear nuevo lote"""
        db_obj = ProductLote(
            lubricentro_id=lubricentro_id,
            producto_id=obj_in.producto_id,
            cantidad=obj_in.cantidad,
            fecha_vencimiento=obj_in.fecha_vencimiento,
            compra_id=obj_in.compra_id
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def create_or_add(
        self,
        db: Session,
        *,
        lubricentro_id: int,
        producto_id: int,
        cantidad: float,
        fecha_vencimiento: Optional[str] = None,
        compra_id: Optional[int] = None
    ) -> ProductLote:
        """
        Crear un nuevo lote o sumar cantidad a uno existente con la misma fecha de vencimiento.
        """
        # Buscar lote existente con misma fecha
        existing = db.query(ProductLote).filter(
            ProductLote.lubricentro_id == lubricentro_id,
            ProductLote.producto_id == producto_id,
            ProductLote.fecha_vencimiento == fecha_vencimiento
        ).first()
        
        if existing:
            existing.cantidad += cantidad
            db.commit()
            db.refresh(existing)
            return existing
        
        # Crear nuevo lote
        db_obj = ProductLote(
            lubricentro_id=lubricentro_id,
            producto_id=producto_id,
            cantidad=cantidad,
            fecha_vencimiento=fecha_vencimiento,
            compra_id=compra_id
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def update(
        self,
        db: Session,
        *,
        db_obj: ProductLote,
        obj_in: ProductLoteUpdate
    ) -> ProductLote:
        """Actualizar lote"""
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def reduce_stock_fifo(
        self,
        db: Session,
        *,
        lubricentro_id: int,
        producto_id: int,
        cantidad: float
    ) -> float:
        """
        Reducir stock usando FIFO (primero los lotes que vencen primero).
        Retorna la cantidad efectivamente reducida.
        """
        lotes = self.get_by_product(db, lubricentro_id=lubricentro_id, producto_id=producto_id)
        cantidad_restante = cantidad
        
        for lote in lotes:
            if cantidad_restante <= 0:
                break
            
            if lote.cantidad >= cantidad_restante:
                lote.cantidad -= cantidad_restante
                cantidad_restante = 0
            else:
                cantidad_restante -= lote.cantidad
                lote.cantidad = 0
        
        db.commit()
        return cantidad - cantidad_restante
    
    def get_total_by_product(
        self,
        db: Session,
        *,
        lubricentro_id: int,
        producto_id: int
    ) -> dict:
        """
        Obtener total de stock y cantidad de lotes para un producto.
        """
        result = db.query(
            func.sum(ProductLote.cantidad).label('total'),
            func.count(ProductLote.id).label('num_lotes')
        ).filter(
            ProductLote.lubricentro_id == lubricentro_id,
            ProductLote.producto_id == producto_id,
            ProductLote.cantidad > 0
        ).first()
        
        return {
            "total": result.total or 0,
            "num_lotes": result.num_lotes or 0
        }
    
    def enrich_with_vencimiento(self, lote: ProductLote) -> dict:
        """Agregar información de vencimiento al lote"""
        estado = calcular_estado_vencimiento(lote.fecha_vencimiento)
        return {
            "id": lote.id,
            "lubricentro_id": lote.lubricentro_id,
            "producto_id": lote.producto_id,
            "cantidad": lote.cantidad,
            "fecha_vencimiento": lote.fecha_vencimiento,
            "fecha_ingreso": lote.fecha_ingreso,
            "compra_id": lote.compra_id,
            "estado_vencimiento": estado["estado"],
            "dias_restantes": estado["dias"],
            "texto_vencimiento": estado["texto"]
        }


product_lote = CRUDProductLote()
