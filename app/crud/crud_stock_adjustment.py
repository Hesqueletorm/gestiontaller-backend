"""
CRUD operations para Ajustes de Stock
Maneja egresos controlados: vencimiento, descarte, consumo interno
"""
from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.crud.base import CRUDBase
from app.models.inventory import StockAdjustment, Producto
from app.schemas.stock_adjustment_schema import StockAdjustmentCreate, StockAdjustmentUpdate


class CRUDStockAdjustment(CRUDBase[StockAdjustment, StockAdjustmentCreate, StockAdjustmentUpdate]):
    
    def create_and_adjust_stock(
        self,
        db: Session,
        *,
        obj_in: StockAdjustmentCreate,
        lubricentro_id: int,
        user_id: Optional[int] = None
    ) -> StockAdjustment:
        """
        Crear ajuste de stock y restar cantidad del producto.
        Valida que el producto exista y tenga suficiente stock.
        """
        # Verificar que el producto existe y pertenece al lubricentro
        producto = db.query(Producto).filter(
            Producto.id == obj_in.producto_id,
            Producto.lubricentro_id == lubricentro_id
        ).first()
        
        if not producto:
            raise ValueError("Producto no encontrado o no pertenece a este lubricentro")
        
        # Verificar stock suficiente
        if producto.cantidad < obj_in.cantidad:
            raise ValueError(f"Stock insuficiente. Disponible: {producto.cantidad}, Solicitado: {obj_in.cantidad}")
        
        # Crear registro de ajuste
        db_obj = StockAdjustment(
            lubricentro_id=lubricentro_id,
            producto_id=obj_in.producto_id,
            tipo_ajuste=obj_in.tipo_ajuste.value,  # Convertir enum a string
            cantidad=obj_in.cantidad,
            motivo=obj_in.motivo,
            created_by=user_id
        )
        db.add(db_obj)
        
        # Restar cantidad del producto
        producto.cantidad -= obj_in.cantidad
        db.add(producto)
        
        db.commit()
        db.refresh(db_obj)
        
        return db_obj
    
    def get_filtered(
        self,
        db: Session,
        *,
        lubricentro_id: int,
        producto_id: Optional[int] = None,
        tipo_ajuste: Optional[str] = None,
        fecha_desde: Optional[datetime] = None,
        fecha_hasta: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 25,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Obtener ajustes con filtros y paginación.
        Incluye datos del producto para mostrar en UI.
        """
        query = db.query(
            StockAdjustment,
            Producto.nombre.label("producto_nombre"),
            Producto.codigo.label("producto_codigo")
        ).join(
            Producto, StockAdjustment.producto_id == Producto.id
        ).filter(
            StockAdjustment.lubricentro_id == lubricentro_id
        )
        
        if producto_id:
            query = query.filter(StockAdjustment.producto_id == producto_id)
        
        if tipo_ajuste:
            query = query.filter(StockAdjustment.tipo_ajuste == tipo_ajuste)
        
        if fecha_desde:
            query = query.filter(StockAdjustment.fecha >= fecha_desde)
        
        if fecha_hasta:
            query = query.filter(StockAdjustment.fecha <= fecha_hasta)
        
        # Contar total
        total = query.count()
        
        # Ordenar y paginar
        results = (
            query
            .order_by(StockAdjustment.fecha.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        
        # Convertir a diccionarios con datos del producto
        items = []
        for adjustment, prod_nombre, prod_codigo in results:
            item = {
                "id": adjustment.id,
                "lubricentro_id": adjustment.lubricentro_id,
                "producto_id": adjustment.producto_id,
                "tipo_ajuste": adjustment.tipo_ajuste,
                "cantidad": adjustment.cantidad,
                "motivo": adjustment.motivo,
                "fecha": adjustment.fecha,
                "created_by": adjustment.created_by,
                "producto_nombre": prod_nombre,
                "producto_codigo": prod_codigo
            }
            items.append(item)
        
        return items, total
    
    def get_stats(
        self,
        db: Session,
        *,
        lubricentro_id: int
    ) -> Dict[str, Any]:
        """
        Obtener estadísticas de ajustes por tipo.
        """
        # Contar por tipo y sumar cantidades
        stats = db.query(
            StockAdjustment.tipo_ajuste,
            func.count(StockAdjustment.id).label("total"),
            func.sum(StockAdjustment.cantidad).label("cantidad")
        ).filter(
            StockAdjustment.lubricentro_id == lubricentro_id
        ).group_by(
            StockAdjustment.tipo_ajuste
        ).all()
        
        result = {
            "total_vencimiento": 0,
            "total_descarte": 0,
            "total_consumo_interno": 0,
            "cantidad_vencimiento": 0.0,
            "cantidad_descarte": 0.0,
            "cantidad_consumo_interno": 0.0
        }
        
        for tipo, total, cantidad in stats:
            result[f"total_{tipo}"] = total
            result[f"cantidad_{tipo}"] = float(cantidad) if cantidad else 0.0
        
        return result


stock_adjustment = CRUDStockAdjustment(StockAdjustment)
