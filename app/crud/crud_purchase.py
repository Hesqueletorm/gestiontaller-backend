"""
CRUD operations para Compras (Purchases)
Incluye lógica para actualizar stock automáticamente y crear lotes
"""
from typing import List, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, extract

from app.crud.base import CRUDBase
from app.models.purchase import Purchase, PurchaseItem
from app.models.inventory import Producto
from app.schemas.purchase_schema import PurchaseCreate, PurchaseItemCreate
from app.crud.crud_product_lote import product_lote as crud_lote


class CRUDPurchase(CRUDBase[Purchase, PurchaseCreate, PurchaseCreate]):
    
    def create_with_items(
        self,
        db: Session,
        *,
        obj_in: PurchaseCreate,
        lubricentro_id: int,
        user_id: Optional[int] = None
    ) -> Purchase:
        """
        Crear una compra con sus items, actualizar el stock y crear lotes.
        """
        # Calcular totales
        subtotal = 0.0
        iva_total = 0.0
        
        for item in obj_in.items:
            item_subtotal = item.cantidad * item.precio_unitario
            item_iva = item_subtotal * (item.iva_porcentaje / 100)
            subtotal += item_subtotal
            iva_total += item_iva
        
        total = subtotal + iva_total
        
        # Crear la compra
        db_purchase = Purchase(
            lubricentro_id=lubricentro_id,
            fecha=obj_in.fecha or datetime.now(),
            numero_factura=obj_in.numero_factura,
            proveedor_nombre=obj_in.proveedor_nombre,
            proveedor_cuit=obj_in.proveedor_cuit,
            proveedor_telefono=obj_in.proveedor_telefono,
            proveedor_email=obj_in.proveedor_email,
            metodo_pago=obj_in.metodo_pago,
            subtotal=subtotal,
            iva=iva_total,
            total=total,
            observaciones=obj_in.observaciones,
            created_by=user_id
        )
        db.add(db_purchase)
        db.flush()  # Para obtener el ID
        
        # Crear items y actualizar stock
        for item in obj_in.items:
            item_subtotal = item.cantidad * item.precio_unitario
            item_iva = item_subtotal * (item.iva_porcentaje / 100)
            item_total = item_subtotal + item_iva
            
            db_item = PurchaseItem(
                compra_id=db_purchase.id,
                producto_id=item.producto_id,
                articulo=item.articulo,
                codigo=item.codigo,
                cantidad=item.cantidad,
                precio_unitario=item.precio_unitario,
                iva_porcentaje=item.iva_porcentaje,
                subtotal=item_subtotal,
                total=item_total
            )
            db.add(db_item)
            
            # Actualizar stock del producto
            if item.producto_id:
                producto = db.query(Producto).filter(Producto.id == item.producto_id).first()
                if producto:
                    # Sumar al stock total del producto
                    producto.cantidad = (producto.cantidad or 0) + item.cantidad
                    
                    # Crear o actualizar lote con la fecha de vencimiento
                    crud_lote.create_or_add(
                        db,
                        lubricentro_id=lubricentro_id,
                        producto_id=item.producto_id,
                        cantidad=item.cantidad,
                        fecha_vencimiento=item.fecha_vencimiento,
                        compra_id=db_purchase.id
                    )
        
        db.commit()
        db.refresh(db_purchase)
        return db_purchase
    
    def get_filtered(
        self,
        db: Session,
        *,
        lubricentro_id: int,
        proveedor: Optional[str] = None,
        fecha_desde: Optional[datetime] = None,
        fecha_hasta: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 25,
    ) -> Tuple[List[Purchase], int]:
        """
        Obtener compras con filtros y paginación
        """
        query = db.query(Purchase).filter(Purchase.lubricentro_id == lubricentro_id)
        
        # Filtro por proveedor
        if proveedor:
            query = query.filter(Purchase.proveedor_nombre.ilike(f"%{proveedor}%"))
        
        # Filtro por fechas
        if fecha_desde:
            query = query.filter(Purchase.fecha >= fecha_desde)
        if fecha_hasta:
            query = query.filter(Purchase.fecha <= fecha_hasta)
        
        # Contar total
        total = query.count()
        
        # Ordenar y paginar
        purchases = (
            query
            .order_by(desc(Purchase.fecha))
            .offset(skip)
            .limit(limit)
            .all()
        )
        
        return purchases, total
    
    def get_with_items(self, db: Session, *, id: int) -> Optional[Purchase]:
        """Obtener compra con sus items"""
        return db.query(Purchase).filter(Purchase.id == id).first()
    
    def delete_and_revert_stock(self, db: Session, *, id: int) -> bool:
        """
        Eliminar compra y revertir el stock
        """
        purchase = db.query(Purchase).filter(Purchase.id == id).first()
        if not purchase:
            return False
        
        # Revertir stock de cada item
        for item in purchase.items:
            if item.producto_id:
                producto = db.query(Producto).filter(Producto.id == item.producto_id).first()
                if producto:
                    producto.cantidad = max(0, (producto.cantidad or 0) - item.cantidad)
        
        # Eliminar la compra (cascade elimina items)
        db.delete(purchase)
        db.commit()
        return True
    
    def get_stats(self, db: Session, *, lubricentro_id: int) -> dict:
        """
        Obtener estadísticas de compras
        """
        # Total de compras y monto
        total_query = db.query(
            func.count(Purchase.id).label('count'),
            func.coalesce(func.sum(Purchase.total), 0).label('monto')
        ).filter(Purchase.lubricentro_id == lubricentro_id).first()
        
        # Compras del mes actual
        hoy = datetime.now()
        primer_dia_mes = hoy.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        mes_query = db.query(
            func.count(Purchase.id).label('count'),
            func.coalesce(func.sum(Purchase.total), 0).label('monto')
        ).filter(
            Purchase.lubricentro_id == lubricentro_id,
            Purchase.fecha >= primer_dia_mes
        ).first()
        
        # Proveedor más frecuente
        proveedor_query = db.query(
            Purchase.proveedor_nombre,
            func.count(Purchase.id).label('count')
        ).filter(
            Purchase.lubricentro_id == lubricentro_id
        ).group_by(
            Purchase.proveedor_nombre
        ).order_by(
            desc('count')
        ).first()
        
        return {
            "total_compras": total_query.count if total_query else 0,
            "monto_total": float(total_query.monto) if total_query else 0,
            "compras_mes_actual": mes_query.count if mes_query else 0,
            "monto_mes_actual": float(mes_query.monto) if mes_query else 0,
            "proveedor_mas_frecuente": proveedor_query[0] if proveedor_query else None
        }
    
    def get_proveedores(self, db: Session, *, lubricentro_id: int) -> List[str]:
        """Obtener lista de proveedores únicos"""
        results = db.query(Purchase.proveedor_nombre).filter(
            Purchase.lubricentro_id == lubricentro_id
        ).distinct().order_by(Purchase.proveedor_nombre).all()
        return [r[0] for r in results]


# Instancia del CRUD
purchase = CRUDPurchase(Purchase)
